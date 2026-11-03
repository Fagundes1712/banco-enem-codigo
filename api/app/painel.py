"""Painel do desenvolvedor: só totais, atrás do Cloudflare Access, de código TOTP e de sessão curta.

Sem token válido do Access, toda rota responde 404, como se não existisse.
"""

import base64
import hashlib
import hmac
import struct
import time
from functools import lru_cache
from pathlib import Path
from typing import Annotated

import jwt
from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from . import servicos
from .auditoria import evento
from .auth import Banco, ip_do_cliente, limita, usuario_atual
from .config import config
from .db import soma_uso
from .pagamentos import assinatura_ativa

SESSAO_SEGUNDOS = 3600
PERIODOS = {"semana": "week", "mes": "month", "ano": "year"}
ARQUIVOS = Path(__file__).parent / "painel_site"


@lru_cache
def _chaves() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"https://{config().painel_access_time}.cloudflareaccess.com/cdn-cgi/access/certs")


def _exige_access(request: Request) -> None:
    c = config()
    token = request.headers.get("cf-access-jwt-assertion", "")
    if not c.painel_email or not token:
        raise HTTPException(404)
    try:
        dados = jwt.decode(
            token,
            _chaves().get_signing_key_from_jwt(token).key,
            algorithms=["RS256"],
            audience=c.painel_access_aud,
            issuer=f"https://{c.painel_access_time}.cloudflareaccess.com",
        )
    except jwt.PyJWTError:
        raise HTTPException(404) from None
    if dados.get("email") != c.painel_email:
        raise HTTPException(404)


router = APIRouter(prefix="/painel", dependencies=[Depends(_exige_access)])
uso = APIRouter()


def codigo_totp(segredo: str, passo: int) -> str:
    """RFC 6238: o mesmo código que o app autenticador mostra."""
    resumo = hmac.new(base64.b32decode(segredo), struct.pack(">Q", passo), "sha1").digest()
    inicio = resumo[-1] & 15
    return f"{(int.from_bytes(resumo[inicio : inicio + 4], 'big') & 0x7FFFFFFF) % 1_000_000:06d}"


def _totp_certo(codigo: str) -> bool:
    passo = int(time.time()) // 30
    return any(hmac.compare_digest(codigo_totp(config().painel_totp, passo + d), codigo) for d in (-1, 0, 1))


def _chave_sessao() -> str:
    # Derivada: um token de login comum nunca abre o painel.
    return hashlib.sha256(b"painel:" + config().jwt_secret.encode()).hexdigest()


def _exige_sessao(painel: Annotated[str | None, Cookie()] = None) -> None:
    try:
        jwt.decode(painel or "", _chave_sessao(), algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Entre com o código.") from None


class Entrada(BaseModel):
    codigo: str = Field(pattern=r"^\d{6}$")


@router.post("/entrar")
def entrar(dados: Entrada, request: Request, resposta: Response, fila: BackgroundTasks):
    c = config()
    if request.headers.get("origin") != c.painel_url:
        raise HTTPException(403, "Origem não permitida.")
    limita("painel-entrar", 5, 900)
    # O mesmo código não serve duas vezes.
    if not _totp_certo(dados.codigo) or not servicos.permite(f"painel-codigo:{dados.codigo}", 1, 120):
        evento("painel_codigo_errado")
        raise HTTPException(401, "Código incorreto.")
    agora = int(time.time())
    sessao = jwt.encode({"iat": agora, "exp": agora + SESSAO_SEGUNDOS}, _chave_sessao(), algorithm="HS256")
    resposta.set_cookie(
        "painel", sessao, max_age=SESSAO_SEGUNDOS, path="/painel", httponly=True, secure=c.producao, samesite="strict"
    )
    evento("painel_entrada")
    fila.add_task(servicos.envia_email, c.painel_email, "Entrada no painel", "Alguém entrou no painel do Banco ENEM agora. Se não foi você, troque a senha do seu e-mail e o código do autenticador.")
    return {"ok": True}


@lru_cache
def _motor_totais():
    return create_engine(config().painel_database_url, pool_pre_ping=True)


def totais(periodo: str) -> dict:
    """Só com o papel painel_leitura, que não lê tabela: as funções do banco devolvem totais."""
    with _motor_totais().connect() as c:

        def linhas(sql: str) -> list[dict]:
            return [dict(x._mapping) for x in c.execute(text(sql), {"p": periodo})]

        return {
            "contas": linhas("SELECT * FROM painel_contas(:p)"),
            "faturamento": linhas("SELECT * FROM painel_faturamento(:p)"),
            "uso": linhas("SELECT * FROM painel_uso(:p)"),
            "assinantes": linhas("SELECT * FROM painel_assinantes()"),
            "conversao": linhas("SELECT * FROM painel_conversao()")[0],
        }


@router.get("/totais", dependencies=[Depends(_exige_sessao)])
def rota_totais(periodo: str = "mes"):
    if periodo not in PERIODOS:
        raise HTTPException(400, "Período inválido.")
    return totais(PERIODOS[periodo])


@router.get("")
def pagina():
    return FileResponse(ARQUIVOS / "painel.html")


@router.get("/painel.js")
def script():
    return FileResponse(ARQUIVOS / "painel.js", media_type="text/javascript")


@router.get("/painel.css")
def estilo():
    return FileResponse(ARQUIVOS / "painel.css")


class Uso(BaseModel):
    questoes: int = Field(ge=1, le=180)
    minutos: int = Field(ge=0, le=600)


@uso.post("/uso", status_code=204)
def registra_uso(dados: Uso, request: Request, banco: Banco, acesso: Annotated[str | None, Cookie()] = None):
    """Fim do simulado: só duas somas, sem conta, questões nem respostas."""
    limita(f"uso:{ip_do_cliente(request)}", 20, 3600)
    try:
        pro = bool(acesso) and assinatura_ativa(usuario_atual(banco, acesso))
    except HTTPException:
        pro = False
    soma_uso(banco, "pro" if pro else "gratis", dados.questoes, dados.minutos)
    banco.commit()
