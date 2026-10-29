import os
import tempfile

SITE = "http://localhost:8765"
_pasta = tempfile.mkdtemp()
os.environ.update(
    AMBIENTE="teste",
    # O CI também roda com PostgreSQL de verdade (TESTE_DATABASE_URL).
    DATABASE_URL=os.environ.get("TESTE_DATABASE_URL") or f"sqlite:///{_pasta}/teste.db",
    REDIS_URL="",
    JWT_SECRET="x" * 40,
    SITE_URL=SITE,
    TURNSTILE_SECRET="teste",
    RESEND_API_KEY="",
    ABACATEPAY_API_KEY="teste",
    ABACATEPAY_WEBHOOK_SECRET="segredo-do-webhook-teste",
    ABACATEPAY_DEV_MODE="true",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import abacatepay, servicos  # noqa: E402
from app.db import Base, motor  # noqa: E402
from app.main import app  # noqa: E402


class AbacateFalsa:
    """Imita a AbacatePay: cada checkout criado fica PENDING até o teste marcar como pago."""

    def __init__(self):
        self.checkouts: dict[str, dict] = {}
        self.preco_produto: dict[str, int] = {}

    def cria_produto(self, id_externo, nome, centavos):
        self.preco_produto[id_externo] = centavos
        return id_externo

    def cria_checkout(self, produto_id, id_externo, url_volta):
        cid = f"bill_{len(self.checkouts) + 1}"
        self.checkouts[cid] = {"status": "PENDING", "amount": self.preco_produto[produto_id], "paidAmount": None}
        return {"id": cid, "url": f"https://pay.exemplo/{cid}", "amount": self.preco_produto[produto_id]}

    def consulta_checkout(self, cid):
        if cid not in self.checkouts:
            raise abacatepay.AbacatePayErro("não encontrado", 404)
        return dict(self.checkouts[cid])

    def paga(self, cid, valor=None):
        c = self.checkouts[cid]
        c.update(status="PAID", paidAmount=valor if valor is not None else c["amount"])


@pytest.fixture
def emails(monkeypatch):
    caixa = []
    monkeypatch.setattr(servicos, "envia_email", lambda para, assunto, texto: caixa.append((para, assunto, texto)))
    monkeypatch.setattr(servicos, "verifica_turnstile", lambda token, ip: token == "ok")
    servicos._limitador.cache_clear()
    return caixa


@pytest.fixture
def abacate(monkeypatch):
    falsa = AbacateFalsa()
    for nome in ("cria_produto", "cria_checkout", "consulta_checkout"):
        monkeypatch.setattr(abacatepay, nome, getattr(falsa, nome))
    return falsa


@pytest.fixture
def cliente(emails):
    Base.metadata.drop_all(motor())
    with TestClient(app, headers={"Origin": SITE}) as c:
        yield c


def link(texto: str, chave: str) -> str:
    return texto.split(f"?{chave}=")[1].split()[0]


@pytest.fixture
def logado(cliente, emails):
    """Cria, confirma e entra numa conta; devolve o cliente com os cookies."""
    cliente.post("/auth/cadastro", json={"email": "aluno@exemplo.com", "senha": "senha-forte-1", "turnstile": "ok", "aceite_termos": True})
    cliente.post("/auth/confirmar", json={"token": link(emails[-1][2], "confirmar")})
    r = cliente.post("/auth/login", json={"email": "aluno@exemplo.com", "senha": "senha-forte-1", "turnstile": "ok"})
    assert r.status_code == 200
    return cliente
