"""Só no PostgreSQL com papéis e migrações (CI): prova que uma conta não enxerga dados de outra."""

import os
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import NullPool

from app.db import (
    Movimento,
    Pagamento,
    Sessao,
    TokenEmail,
    Usuario,
    _fabrica,
    agora,
    assume_dono,
    define_usuario,
    motor,
    soma_uso,
)

pytestmark = pytest.mark.skipif(motor().dialect.name != "postgresql", reason="RLS só existe no PostgreSQL")

COM_DONO = (Usuario, Sessao, TokenEmail, Pagamento, Movimento)


def _conta(email: str) -> str:
    uid = str(uuid.uuid4())
    fim = agora() + timedelta(days=1)
    with _fabrica()() as s:
        define_usuario(s, uid)
        s.add(Usuario(id=uid, email=email, senha_hash="x" * 60, termos_versao="t"))
        s.flush()
        s.add(Sessao(usuario_id=uid, token_hash=f"sessao-{uid}", expira_em=fim))
        s.add(TokenEmail(usuario_id=uid, tipo="senha", token_hash=f"token-{uid}", expira_em=fim))
        s.add(Pagamento(id=uid, usuario_id=uid, plano="mensal", checkout_id=f"bill-{uid}", valor_centavos=2499, dias=30))
        s.add(Movimento(usuario_id=uid, pagamento_id=uid, evento="criado", valor_centavos=2499))
        s.commit()
    return uid


@pytest.fixture
def contas(banco_limpo):
    return _conta("a@exemplo.com"), _conta("b@exemplo.com")


def test_sem_usuario_nao_ve_nada(contas):
    with _fabrica()() as s:
        for tabela in COM_DONO:
            assert s.scalars(select(tabela)).all() == [], tabela.__name__


def test_consulta_sem_filtro_so_traz_a_propria_conta(contas):
    a, _b = contas
    with _fabrica()() as s:
        define_usuario(s, a)
        assert [u.id for u in s.scalars(select(Usuario))] == [a]
        for tabela in (Sessao, TokenEmail, Pagamento, Movimento):
            assert [x.usuario_id for x in s.scalars(select(tabela))] == [a], tabela.__name__


def test_usuario_continua_depois_do_commit(contas):
    a, _b = contas
    with _fabrica()() as s:
        define_usuario(s, a)
        s.commit()
        assert s.scalar(select(Usuario.id)) == a
        s.rollback()
        assert s.scalar(select(Usuario.id)) == a


def test_nao_altera_nem_apaga_dados_de_outro(contas):
    a, b = contas
    with _fabrica()() as s:
        define_usuario(s, a)
        assert s.execute(update(Usuario).where(Usuario.id == b).values(confirmado=True)).rowcount == 0
        assert s.execute(text("DELETE FROM sessoes WHERE usuario_id = :b"), {"b": b}).rowcount == 0
        s.commit()


def test_nao_grava_em_nome_de_outro(contas):
    a, b = contas
    with _fabrica()() as s:
        define_usuario(s, a)
        s.add(Sessao(usuario_id=b, token_hash="roubo", expira_em=agora()))
        with pytest.raises(DBAPIError, match="row-level security"):
            s.commit()


@pytest.mark.parametrize("sql", ["UPDATE movimentos SET valor_centavos = 1", "DELETE FROM movimentos"])
def test_trilha_de_pagamentos_e_so_de_inclusao(contas, sql):
    with _fabrica()() as s:
        define_usuario(s, contas[0])
        with pytest.raises(DBAPIError, match="permission denied"):
            s.execute(text(sql))


@pytest.mark.parametrize(
    "sql",
    [
        "CREATE TABLE invasao (id int)",
        "DROP TABLE usuarios",
        "ALTER TABLE usuarios DISABLE ROW LEVEL SECURITY",
        "SET ROLE api_busca",
        "SET ROLE api_migracao",
        "TRUNCATE usuarios CASCADE",
    ],
)
def test_api_nao_muda_o_banco_nem_troca_de_papel(banco_limpo, sql):
    with _fabrica()() as s, pytest.raises(DBAPIError):
        s.execute(text(sql))


def test_papel_da_api_nao_ignora_o_rls(banco_limpo):
    with _fabrica()() as s:
        papel = s.execute(text("SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")).one()
    assert tuple(papel) == ("api_app", False, False)


def test_toda_tabela_tem_rls_forcado(banco_limpo):
    # Uma tabela nova sem RLS quebra este teste: não dá para esquecer.
    sql = """SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
             WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname <> 'alembic_version'
               AND NOT (c.relrowsecurity AND c.relforcerowsecurity)"""
    with _fabrica()() as s:
        assert s.scalars(text(sql)).all() == []
        assert s.scalar(text("SELECT count(*) FROM pg_policies WHERE schemaname = 'public'")) >= 6


def test_funcoes_de_busca_so_devolvem_o_id(contas):
    a, _b = contas
    with _fabrica()() as s:
        assert assume_dono(s, "email", "a@exemplo.com") == a
        assert assume_dono(s, "sessao", f"sessao-{a}") == a
        assert assume_dono(s, "token_email", f"token-{a}") == a
        assert assume_dono(s, "checkout", f"bill-{a}") == a
        assert assume_dono(s, "email", "ninguem@exemplo.com") is None


def test_funcoes_de_busca_sao_trancadas(banco_limpo):
    sql = """SELECT p.proname, p.prosecdef, array_to_string(p.proconfig, ','), pg_get_userbyid(p.proowner),
                    has_function_privilege('public', p.oid, 'EXECUTE')
             FROM pg_proc p WHERE p.proname IN ('conta_por_email', 'dono_token_email', 'dono_sessao', 'dono_checkout')"""
    with _fabrica()() as s:
        funcoes = s.execute(text(sql)).all()
    assert len(funcoes) == 4
    for _nome, definer, ajustes, dono, publico in funcoes:
        assert definer and "search_path=public" in ajustes and dono == "api_busca" and not publico


def test_login_de_ponta_a_ponta_com_duas_contas(cliente, emails):
    # O caminho real, pela API: cada um entra e só vê os próprios dados.
    def entra(email):
        cliente.cookies.clear()
        corpo = {"email": email, "senha": "senha-forte-1", "turnstile": "ok", "aceite_termos": True}
        assert cliente.post("/auth/cadastro", json=corpo).status_code == 202
        token = emails[-1][2].split("?confirmar=")[1].split()[0]
        assert cliente.post("/auth/confirmar", json={"token": token, "senha": "senha-forte-1"}).status_code == 200
        assert cliente.post("/auth/login", json={"email": email, "senha": "senha-forte-1", "turnstile": "ok"}).status_code == 200

    entra("a@exemplo.com")
    assert cliente.get("/conta/dados").json()["conta"]["email"] == "a@exemplo.com"
    entra("b@exemplo.com")
    dados = cliente.get("/conta/dados").json()
    assert dados["conta"]["email"] == "b@exemplo.com" and len(dados["sessoes"]) == 1


@pytest.fixture
def leitura():
    motor_painel = create_engine(os.environ["TESTE_PAINEL_DATABASE_URL"], poolclass=NullPool)
    with motor_painel.connect() as c:
        yield c


@pytest.mark.parametrize("tabela", ["usuarios", "pagamentos", "sessoes", "tokens_email", "movimentos", "produtos", "uso_diario"])
def test_painel_nao_le_tabela_nenhuma(banco_limpo, leitura, tabela):
    with pytest.raises(DBAPIError, match="permission denied"):
        leitura.execute(text(f"SELECT * FROM {tabela}"))  # noqa: S608


@pytest.mark.parametrize("funcao", ["conta_por_email('a@exemplo.com')", "dono_sessao('x')", "soma_uso('pro', 1, 1)"])
def test_painel_nao_chama_funcoes_da_api(banco_limpo, leitura, funcao):
    with pytest.raises(DBAPIError, match="permission denied"):
        leitura.execute(text(f"SELECT {funcao}"))


def test_painel_ve_so_totais(contas, leitura):
    a, _b = contas
    with _fabrica()() as s:
        define_usuario(s, a)
        s.execute(update(Usuario).values(confirmado=True))
        s.execute(update(Pagamento).values(status="pago", pago_em=agora()))
        s.commit()
    assert leitura.execute(text("SELECT total FROM painel_contas('month')")).scalar() == 1
    assert leitura.execute(text("SELECT pagamentos, centavos FROM painel_faturamento('year')")).one() == (1, 2499)
    assert tuple(leitura.execute(text("SELECT * FROM painel_conversao()")).one()) == (1, 1)
    assert tuple(leitura.execute(text("SELECT plano, nao_renovaram FROM painel_assinantes()")).one()) == ("mensal", 1)
    with pytest.raises(DBAPIError):
        leitura.execute(text("SELECT email FROM painel_contas('month')"))


def test_uso_soma_pela_funcao_e_api_nao_le(banco_limpo, leitura):
    with _fabrica()() as s:
        soma_uso(s, "gratis", 10, 20)
        soma_uso(s, "gratis", 5, 7)
        s.commit()
        with pytest.raises(DBAPIError, match="permission denied"):
            s.execute(text("SELECT * FROM uso_diario"))
    assert tuple(leitura.execute(text("SELECT plano, questoes, minutos FROM painel_uso('year')")).one()) == ("gratis", 15, 27)


def test_rota_de_uso_grava_no_banco(cliente, leitura):
    assert cliente.post("/uso", json={"questoes": 3, "minutos": 4}).status_code == 204
    assert tuple(leitura.execute(text("SELECT plano, questoes FROM painel_uso('year')")).one()) == ("gratis", 3)
