"""Tabelas e sessão do banco (PostgreSQL em produção, SQLite nos testes)."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine
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


@lru_cache
def motor():
    url = config().database_url
    # pool_pre_ping: o Neon desliga conexões paradas; pool pequeno porque cada instância soma conexões.
    extra = {} if url.startswith("sqlite") else {"pool_size": 5, "max_overflow": 5, "pool_pre_ping": True}
    return create_engine(url, **extra)


@lru_cache
def _fabrica():
    return sessionmaker(motor(), expire_on_commit=False)


def criar_tabelas() -> None:
    # shortcut: create_all não altera tabelas existentes; adotar Alembic antes da primeira mudança de schema em produção.
    Base.metadata.create_all(motor())


def sessao() -> Iterator[Session]:
    with _fabrica()() as s:
        yield s
