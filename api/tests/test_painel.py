import base64
import os
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app import painel
from app.config import config
from app.db import UsoDiario, _fabrica, motor
from conftest import SITE

SEGREDO = base64.b32encode(b"12345678901234567890").decode()
ORIGEM = "https://painel.exemplo.com"
AJUSTES = {
    "PAINEL_EMAIL": "dono@exemplo.com",
    "PAINEL_URL": ORIGEM,
    "PAINEL_ACCESS_TIME": "time",
    "PAINEL_ACCESS_AUD": "aplicativo",
    "PAINEL_TOTP": SEGREDO,
    "PAINEL_DATABASE_URL": "sqlite://",
}
CHAVE = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def selo(**troca):
    dados = {
        "email": "dono@exemplo.com",
        "aud": "aplicativo",
        "iss": "https://time.cloudflareaccess.com",
        "exp": int(time.time()) + 60,
    } | troca
    return {"Cf-Access-Jwt-Assertion": jwt.encode(dados, CHAVE, algorithm="RS256"), "Origin": ORIGEM}


def codigo_agora():
    return painel.codigo_totp(SEGREDO, int(time.time()) // 30)


@pytest.fixture
def ligado(cliente, monkeypatch):
    for nome, valor in AJUSTES.items():
        monkeypatch.setenv(nome, valor)
    config.cache_clear()

    class Chaves:
        def get_signing_key_from_jwt(self, _token):
            return type("Chave", (), {"key": CHAVE.public_key()})

    monkeypatch.setattr(painel, "_chaves", Chaves)
    monkeypatch.setattr(painel, "totais", lambda p: {"periodo": p})
    yield cliente
    monkeypatch.undo()
    config.cache_clear()


def test_totp_bate_com_o_vetor_da_rfc_6238():
    assert painel.codigo_totp(SEGREDO, 1) == "287082"


def test_desligado_responde_404_mesmo_com_selo(cliente):
    assert cliente.get("/painel", headers=selo()).status_code == 404


@pytest.mark.parametrize(
    "cabecalhos",
    [
        {},
        {"Cf-Access-Jwt-Assertion": "lixo"},
        selo(email="outro@exemplo.com"),
        selo(aud="outro"),
        selo(iss="https://outro.cloudflareaccess.com"),
        selo(exp=1),
    ],
)
@pytest.mark.parametrize("rota", ["/painel", "/painel/totais", "/painel/painel.js"])
def test_sem_selo_valido_a_rota_nao_existe(ligado, cabecalhos, rota):
    assert ligado.get(rota, headers=cabecalhos).status_code == 404


def test_selo_assinado_com_outra_chave_nao_entra(ligado):
    outra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    dados = {"email": "dono@exemplo.com", "aud": "aplicativo", "iss": "https://time.cloudflareaccess.com"}
    assert ligado.get("/painel", headers={"Cf-Access-Jwt-Assertion": jwt.encode(dados, outra, algorithm="RS256")}).status_code == 404


def test_selo_sem_assinatura_nao_entra(ligado):
    dados = {"email": "dono@exemplo.com", "aud": "aplicativo", "iss": "https://time.cloudflareaccess.com"}
    falso = jwt.encode(dados, "", algorithm="none")
    assert ligado.get("/painel", headers={"Cf-Access-Jwt-Assertion": falso}).status_code == 404


def test_pagina_abre_com_csp_propria(ligado):
    r = ligado.get("/painel", headers=selo())
    assert r.status_code == 200 and "script-src 'self'" in r.headers["content-security-policy"]
    assert "unsafe" not in r.headers["content-security-policy"]


def test_totais_pedem_codigo_e_sessao_vale_so_para_o_painel(ligado, emails):
    assert ligado.get("/painel/totais", headers=selo()).status_code == 401
    assert ligado.post("/painel/entrar", headers=selo(), json={"codigo": "000000"}).status_code == 401

    r = ligado.post("/painel/entrar", headers=selo(), json={"codigo": codigo_agora()})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/painel" in cookie and "domain" not in cookie
    assert ligado.get("/painel/totais?periodo=ano", headers=selo()).json() == {"periodo": "year"}
    assert ligado.get("/painel/totais?periodo=x; DROP", headers=selo()).status_code == 400
    assert emails[-1][0] == "dono@exemplo.com"

    # A sessão sozinha não basta: sem o selo do Access, nada existe.
    assert ligado.get("/painel/totais").status_code == 404


def test_codigo_nao_serve_duas_vezes(ligado):
    corpo = {"codigo": codigo_agora()}
    assert ligado.post("/painel/entrar", headers=selo(), json=corpo).status_code == 200
    assert ligado.post("/painel/entrar", headers=selo(), json=corpo).status_code == 401


def test_entrada_de_outra_origem_e_recusada(ligado):
    cabecalhos = selo() | {"Origin": SITE}
    assert ligado.post("/painel/entrar", headers=cabecalhos, json={"codigo": codigo_agora()}).status_code == 403


def test_tentativas_tem_limite(ligado):
    for _ in range(5):
        ligado.post("/painel/entrar", headers=selo(), json={"codigo": "000000"})
    assert ligado.post("/painel/entrar", headers=selo(), json={"codigo": codigo_agora()}).status_code == 429


def test_login_comum_nao_abre_o_painel(ligado, logado):
    ligado.cookies.set("painel", ligado.cookies.get("acesso"), path="/painel")
    assert ligado.get("/painel/totais", headers=selo()).status_code == 401


def test_nao_ha_rota_que_mude_dados(ligado):
    rotas = [r for r in painel.router.routes if "POST" in r.methods or "DELETE" in r.methods or "PUT" in r.methods]
    assert [r.path for r in rotas] == ["/painel/entrar"]


@pytest.mark.parametrize("corpo", [{"questoes": 0, "minutos": 1}, {"questoes": 181, "minutos": 1}, {"questoes": 1, "minutos": 601}])
def test_uso_recusa_numero_fora_do_limite(cliente, corpo):
    assert cliente.post("/uso", json=corpo).status_code == 422


@pytest.mark.skipif(os.environ.get("TESTE_ADMIN_DATABASE_URL") is not None, reason="o api_app não lê uso_diario; test_rls cobre")
def test_uso_soma_por_plano_sem_conta(cliente):
    assert cliente.post("/uso", json={"questoes": 10, "minutos": 20}).status_code == 204
    assert cliente.post("/uso", json={"questoes": 5, "minutos": 7}).status_code == 204
    with _fabrica()() as s:
        linha = s.query(UsoDiario).one()
    assert (linha.plano, linha.questoes, linha.minutos) == ("gratis", 15, 27)
    assert motor().dialect.name == "sqlite"
