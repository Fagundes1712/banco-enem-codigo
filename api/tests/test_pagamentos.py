import base64
import hashlib
import hmac
import json
from datetime import datetime

from app.abacatepay import CHAVE_PUBLICA_WEBHOOK
from app.db import agora

SEGREDO = "segredo-do-webhook-teste"


def assina(corpo: bytes) -> str:
    return base64.b64encode(hmac.new(CHAVE_PUBLICA_WEBHOOK.encode(), corpo, hashlib.sha256).digest()).decode()


def webhook(cliente, checkout_id, segredo=SEGREDO, dev_mode=True, assinatura=None):
    corpo = json.dumps({"event": "checkout.completed", "devMode": dev_mode, "data": {"checkout": {"id": checkout_id}}}).encode()
    return cliente.post(
        f"/webhooks/abacatepay?webhookSecret={segredo}",
        content=corpo,
        headers={"x-webhook-signature": assinatura or assina(corpo), "Origin": ""},
    )


def compra(cliente, plano="mensal"):
    r = cliente.post("/pagamentos", json={"plano": plano})
    assert r.status_code == 200
    return r.json()["url"].rsplit("/", 1)[1]


def dias_restantes(cliente):
    ate = cliente.get("/me").json()["assinatura_ate"]
    return (datetime.fromisoformat(ate) - agora()).days if ate else 0


def test_planos_com_preco_do_servidor(cliente):
    assert cliente.get("/planos").json() == [
        {"id": "mensal", "centavos": 2499, "dias": 30},
        {"id": "anual", "centavos": 23988, "dias": 365},
    ]


def test_pagar_exige_login(cliente, abacate):
    assert cliente.post("/pagamentos", json={"plano": "mensal"}).status_code == 401


def test_plano_inventado_e_recusado(logado, abacate):
    assert logado.post("/pagamentos", json={"plano": "gratis"}).status_code == 422


def test_webhook_libera_uma_vez_so(logado, abacate):
    cid = compra(logado)
    assert logado.get("/me").json()["assinatura_ativa"] is False
    abacate.paga(cid)
    assert webhook(logado, cid).status_code == 200
    assert webhook(logado, cid).status_code == 200  # aviso repetido
    assert logado.get("/me").json()["assinatura_ativa"] is True
    assert dias_restantes(logado) == 29


def test_volta_do_pagamento_libera_sem_webhook(logado, abacate):
    cid = compra(logado, "anual")
    assert logado.post("/pagamentos/sincronizar").json() == {"assinatura_ativa": False}
    abacate.paga(cid)
    assert logado.post("/pagamentos/sincronizar").json() == {"assinatura_ativa": True}
    assert dias_restantes(logado) == 364


def test_renovar_antes_de_vencer_soma_os_dias(logado, abacate):
    for _ in range(2):
        cid = compra(logado)
        abacate.paga(cid)
        webhook(logado, cid)
    assert dias_restantes(logado) == 59


def test_valor_pago_diferente_nao_libera(logado, abacate):
    cid = compra(logado)
    abacate.paga(cid, valor=1)
    webhook(logado, cid)
    assert logado.get("/me").json()["assinatura_ativa"] is False


def test_webhook_falso_e_recusado(logado, abacate):
    cid = compra(logado)
    abacate.paga(cid)
    assert webhook(logado, cid, segredo="errado").status_code == 401
    assert webhook(logado, cid, assinatura="invalida").status_code == 401
    assert logado.get("/me").json()["assinatura_ativa"] is False


def test_pagamento_de_teste_nao_libera_producao(logado, abacate):
    cid = compra(logado)
    abacate.paga(cid)
    assert webhook(logado, cid, dev_mode=False).status_code == 200
    assert logado.get("/me").json()["assinatura_ativa"] is False


def test_checkout_desconhecido_e_ignorado(logado, abacate):
    assert webhook(logado, "bill_que_nao_existe").status_code == 200
