"""API do Banco ENEM: contas e assinatura. Rodar: uvicorn app.main:app (ver api/README.md)."""

import hmac
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import auth, conta, pagamentos
from .config import config
from .db import criar_tabelas

TAMANHO_MAXIMO = 64 * 1024  # nenhum pedido legítimo passa disso


@asynccontextmanager
async def _inicio(_app):
    config()  # falha cedo se faltar variável
    criar_tabelas()
    yield


app = FastAPI(title="Banco ENEM API", lifespan=_inicio, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def protecoes(request: Request, call_next):
    # Quem chama o endereço do Cloud Run direto pula o Cloudflare (e forja o IP); sem o segredo, nada feito.
    segredo = config().origem_secret
    if segredo and not hmac.compare_digest(request.headers.get("x-origem", ""), segredo):
        return JSONResponse({"detail": "Acesso só pelo domínio do site."}, status_code=403)
    tamanho = request.headers.get("content-length")
    # Sem Content-Length (corpo em pedaços) não dá para saber o tamanho antes de ler: recusa.
    if request.method == "POST" and not tamanho:
        return JSONResponse({"detail": "Envie o tamanho do pedido."}, status_code=411)
    if tamanho and (not tamanho.isdigit() or int(tamanho) > TAMANHO_MAXIMO):
        return JSONResponse({"detail": "Pedido grande demais."}, status_code=413)
    # CSRF: o navegador manda o cookie sozinho, então toda mudança precisa vir do próprio site.
    # O webhook vem da AbacatePay e tem verificação própria.
    if request.method not in ("GET", "HEAD", "OPTIONS") and not request.url.path.startswith("/webhooks/"):
        if request.headers.get("origin") != config().site_url:
            return JSONResponse({"detail": "Origem não permitida."}, status_code=403)
    resposta = await call_next(request)
    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    return resposta


# Adicionado depois do middleware acima, fica por fora: responde o preflight antes da checagem de origem.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config().site_url],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(auth.router)
app.include_router(pagamentos.router)
app.include_router(conta.router)


@app.get("/saude")
def saude():
    return {"ok": True}
