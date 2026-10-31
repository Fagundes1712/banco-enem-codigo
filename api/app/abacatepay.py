"""Cliente da API v2 da AbacatePay (portado de projetos-referencia/pix-creditos)."""

import base64
import hashlib
import hmac
from urllib.parse import urlencode

import httpx

from .config import config

# Teste ou produção é decidido pela chave, não pelo endereço.
BASE_URL = "https://api.abacatepay.com/v2"

# Chave HMAC global publicada pela AbacatePay (docs: webhooks/security). Sendo pública, só prova que o
# corpo não foi alterado; o webhookSecret na URL prova quem enviou, e a API decide o que foi pago.
CHAVE_PUBLICA_WEBHOOK = (
    "t9dXRhHHo3yDEj5pVDYz0frf7q6bMKyMRmxxCPIPp3RCplBfXRxqlC6ZpiWmOqj4L63qEaeUOtrCI8P0VMUgo6iIga2ri9ogaHFs0W"
    "IIywSMg0q7RmBfybe1E5XJcfC4IW3alNqym0tXoAKkzvfEjZxV6bE0oG2zJrNNYmUCKZyV0KZ3JS8Votf9EAWWYdiDkMkpbMdPggfh"
    "1EqHlVkMiTady6jOR3hyzGEHrIz2Ret0xHKMbiqkr9HS1JhNHDX9"
)


class AbacatePayErro(Exception):
    def __init__(self, mensagem: str, status: int | None = None):
        super().__init__(mensagem)
        self.status = status


def _pede(caminho: str, corpo: dict | None = None) -> dict:
    try:
        r = httpx.request(
            "GET" if corpo is None else "POST",
            BASE_URL + caminho,
            headers={"Authorization": f"Bearer {config().abacatepay_api_key}"},
            json=corpo,
            timeout=10,
        )
        dados = r.json().get("data")
    except (httpx.HTTPError, ValueError) as e:
        raise AbacatePayErro(f"AbacatePay {caminho.split('?')[0]} falhou") from e
    if r.status_code >= 400 or not isinstance(dados, dict):
        raise AbacatePayErro(f"AbacatePay {caminho.split('?')[0]} falhou (HTTP {r.status_code})", r.status_code)
    return dados


def cria_produto(id_externo: str, nome: str, centavos: int) -> str:
    dados = _pede("/products/create", {"externalId": id_externo, "name": nome, "price": centavos, "currency": "BRL"})
    return str(dados["id"])


def cria_checkout(produto_id: str, id_externo: str, url_volta: str) -> dict:
    dados = _pede(
        "/checkouts/create",
        {
            "items": [{"id": produto_id, "quantity": 1}],
            "externalId": id_externo,
            "returnUrl": url_volta,
            "completionUrl": url_volta,
            "methods": ["PIX"],
        },
    )
    return {"id": str(dados["id"]), "url": str(dados["url"]), "amount": int(dados["amount"])}


def consulta_checkout(checkout_id: str) -> dict:
    """A fonte da verdade de um pagamento."""
    dados = _pede("/checkouts/get?" + urlencode({"id": checkout_id}))
    pago = dados.get("paidAmount")
    return {"status": str(dados["status"]), "amount": int(dados["amount"]), "paidAmount": None if pago is None else int(pago)}


def _iguais(recebido: str, esperado: str) -> bool:
    # Hash antes de comparar: tempo constante mesmo com tamanhos diferentes.
    return hmac.compare_digest(hashlib.sha256(recebido.encode()).digest(), hashlib.sha256(esperado.encode()).digest())


def webhook_autentico(segredo_url: str, assinatura: str, corpo: bytes) -> bool:
    """Vale só se o segredo da URL e a assinatura do corpo conferem."""
    if not _iguais(segredo_url, config().abacatepay_webhook_secret):
        return False
    esperado = base64.b64encode(hmac.new(CHAVE_PUBLICA_WEBHOOK.encode(), corpo, hashlib.sha256).digest()).decode()
    return _iguais(assinatura, esperado)
