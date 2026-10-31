"""Serviços externos: Turnstile (Cloudflare), e-mail (Resend) e limite de tentativas (Redis)."""

import logging
import time
from functools import lru_cache
from urllib.parse import urlparse

import httpx
import redis

from .config import config

log = logging.getLogger("api")


def verifica_turnstile(token: str, ip: str, acao: str) -> bool:
    if not token:
        return False
    c = config()
    try:
        r = httpx.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": c.turnstile_secret, "response": token, "remoteip": ip},
            timeout=10,
        )
        dados = r.json() if r.status_code == 200 else {}
    except (httpx.HTTPError, ValueError):
        return False
    if dados.get("success") is not True:
        return False
    # Em produção o token tem de vir do nosso site e do formulário certo (as chaves de teste não dizem isso).
    return not c.producao or (dados.get("hostname") == urlparse(c.site_url).hostname and dados.get("action") == acao)


def envia_email(para: str, assunto: str, texto: str) -> None:
    c = config()
    if not c.resend_api_key:
        # Só fora de produção (config exige a chave lá): mostra o e-mail no terminal para testar o fluxo.
        log.warning("E-mail não enviado (sem RESEND_API_KEY) para %s: %s\n%s", para, assunto, texto)
        return
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {c.resend_api_key}"},
        json={"from": c.email_remetente, "to": [para], "subject": assunto, "text": texto},
        timeout=10,
    )
    r.raise_for_status()


class _LimiteMemoria:
    def __init__(self):
        self.contas: dict[str, tuple[int, float]] = {}

    def conta(self, chave: str, janela: int) -> int:
        n, fim = self.contas.get(chave, (0, 0.0))
        if time.monotonic() >= fim:
            n, fim = 0, time.monotonic() + janela
        self.contas[chave] = (n + 1, fim)
        return n + 1


class _LimiteRedis:
    def __init__(self, url: str):
        self.r = redis.Redis.from_url(url, socket_timeout=2)

    def conta(self, chave: str, janela: int) -> int:
        # Cria a chave já com validade e só depois soma: nunca fica um contador sem prazo.
        pipe = self.r.pipeline()
        pipe.set(chave, 0, ex=janela, nx=True)
        pipe.incr(chave)
        return int(pipe.execute()[1])


@lru_cache
def _limitador():
    url = config().redis_url
    return _LimiteRedis(url) if url else _LimiteMemoria()


def permite(chave: str, maximo: int, janela_segundos: int) -> bool:
    """Conta mais uma tentativa e diz se ainda está dentro do limite da janela."""
    return _limitador().conta(f"limite:{chave}", janela_segundos) <= maximo
