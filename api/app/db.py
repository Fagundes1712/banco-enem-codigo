"""Tabelas e sessão do banco (PostgreSQL com RLS em produção, SQLite nos testes locais)."""

import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime
from functools import lru_cache

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, create_engine, event, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import config


def agora() -> datetime:
    # Tudo em UTC sem fuso no banco, para comparar igual no Postgres e no SQLite.
    return datetime.now(UTC).replace(tzinfo=None)


def _id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(60))
    confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
    termos_versao: Mapped[str] = mapped_column(String(20))
    termos_aceitos_em: Mapped[datetime] = mapped_column(DateTime, default=agora)
    assinatura_ate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Tokens de acesso emitidos antes disto deixam de valer (troca de senha, exclusão).
    senha_trocada_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)


class Sessao(Base):
    """Uma sessão = um token de renovação. Guardamos só o hash dele."""

    __tablename__ = "sessoes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime)
    revogada: Mapped[bool] = mapped_column(Boolean, default=False)
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=agora)


class TokenEmail(Base):
    """Link de uso único enviado por e-mail: confirmar conta ou trocar senha."""

    __tablename__ = "tokens_email"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(10))  # confirmar | senha
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime)
    usado: Mapped[bool] = mapped_column(Boolean, default=False)


class Produto(Base):
    """Produto da AbacatePay criado para cada plano."""

    __tablename__ = "produtos"
    plano: Mapped[str] = mapped_column(String(20), primary_key=True)
    abacatepay_id: Mapped[str] = mapped_column(String(100), unique=True)
    valor_centavos: Mapped[int] = mapped_column(Integer)


class Pagamento(Base):
    """Cobrança criada pela API. Valor e dias vêm daqui, nunca do webhook."""

    __tablename__ = "pagamentos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True)
    plano: Mapped[str] = mapped_column(String(20))
    checkout_id: Mapped[str] = mapped_column(String(100), unique=True)
    valor_centavos: Mapped[int] = mapped_column(Integer)
    dias: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="pendente")  # pendente | pago
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)
    pago_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Movimento(Base):
    """Trilha de pagamentos só de inclusão: no banco, a API não tem permissão de editar nem apagar."""

    __tablename__ = "movimentos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    # Sem chave estrangeira: a trilha fica depois de a conta ser excluída, só com o id interno.
    usuario_id: Mapped[str] = mapped_column(String(36), index=True)
    pagamento_id: Mapped[str] = mapped_column(String(36))
    evento: Mapped[str] = mapped_column(String(10))  # criado | pago
    valor_centavos: Mapped[int] = mapped_column(Integer)
    em: Mapped[datetime] = mapped_column(DateTime, default=agora)


class UsoDiario(Base):
    """Só somas por dia e plano: sem conta, questão nem resposta. A API grava por soma_uso e não lê."""

    __tablename__ = "uso_diario"
    dia: Mapped[date] = mapped_column(Date, primary_key=True)
    plano: Mapped[str] = mapped_column(String(10), primary_key=True)  # gratis | pro
    questoes: Mapped[int] = mapped_column(Integer)
    minutos: Mapped[int] = mapped_column(Integer)


@lru_cache
def motor():
    url = config().database_url
    # pool_pre_ping: o Neon desliga conexões paradas; pool pequeno porque cada instância soma conexões.
    extra = {} if url.startswith("sqlite") else {"pool_size": 5, "max_overflow": 5, "pool_pre_ping": True}
    return create_engine(url, **extra)


def _reaplica_usuario(banco, _transacao, conexao) -> None:
    # O set_config vale só para a transação; depois de um commit, a próxima começa sem usuário.
    usuario_id = banco.info.get("usuario_id")
    if usuario_id and conexao.dialect.name == "postgresql":
        conexao.execute(select(func.set_config("app.usuario_id", usuario_id, True)))


@lru_cache
def _fabrica():
    fabrica = sessionmaker(motor(), expire_on_commit=False)
    event.listen(fabrica, "after_begin", _reaplica_usuario)
    return fabrica


def criar_tabelas() -> None:
    # No PostgreSQL quem cria as tabelas é o Alembic (papel api_migracao); a API não tem permissão.
    if motor().dialect.name == "sqlite":
        Base.metadata.create_all(motor())


def define_usuario(banco: Session, usuario_id: str) -> None:
    """Diz ao banco de quem é esta sessão: o RLS só mostra as linhas dessa conta."""
    banco.info["usuario_id"] = usuario_id
    if motor().dialect.name == "postgresql":
        banco.execute(select(func.set_config("app.usuario_id", usuario_id, True)))


# Antes do login não há usuário da vez. Cada busca é uma função estreita do banco que devolve só o id do dono.
_DONOS = {
    "email": (func.conta_por_email, Usuario.id, Usuario.email),
    "token_email": (func.dono_token_email, TokenEmail.usuario_id, TokenEmail.token_hash),
    "sessao": (func.dono_sessao, Sessao.usuario_id, Sessao.token_hash),
    "checkout": (func.dono_checkout, Pagamento.usuario_id, Pagamento.checkout_id),
}


def assume_dono(banco: Session, tipo: str, valor: str) -> str | None:
    """Descobre o dono de um e-mail, token ou checkout e fixa o usuário da sessão. None se não houver."""
    funcao, coluna, chave = _DONOS[tipo]
    postgres = motor().dialect.name == "postgresql"
    usuario_id = banco.scalar(select(funcao(valor)) if postgres else select(coluna).where(chave == valor))
    if usuario_id:
        define_usuario(banco, usuario_id)
    return usuario_id


def soma_uso(banco: Session, plano: str, questoes: int, minutos: int) -> None:
    if motor().dialect.name == "postgresql":
        banco.execute(select(func.soma_uso(plano, questoes, minutos)))
        return
    chave = (agora().date(), plano)
    linha = banco.get(UsoDiario, chave) or UsoDiario(dia=chave[0], plano=plano, questoes=0, minutos=0)
    linha.questoes += questoes
    linha.minutos += minutos
    banco.add(linha)


def sessao() -> Iterator[Session]:
    with _fabrica()() as s:
        yield s
