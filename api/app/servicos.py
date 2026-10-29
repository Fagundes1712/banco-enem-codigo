"""Serviços externos: Turnstile (Cloudflare), e-mail (Resend) e limite de tentativas (Redis)."""

import logging
import time
from functools import lru_cache

import httpx
import redis

from .config import config

log = logging.getLogger("api")


def verifica_turnstile(token: str, ip: str) -> bool:
    if not token:
        return False
    try:
        r = httpx.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": config().turnstile_secret, "response": token, "remoteip": ip},
            timeout=10,
        )
        return r.status_code == 200 and r.json().get("success") is True
    except httpx.HTTPError:
        return False


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
        n = self.r.incr(chave)
        if n == 1:
            self.r.expire(chave, janela)
        return int(n)


@lru_cache
def _limitador():
    url = config().redis_url
    return _LimiteRedis(url) if url else _LimiteMemoria()


def permite(chave: str, maximo: int, janela_segundos: int) -> bool:
    """Conta mais uma tentativa e diz se ainda está dentro do limite da janela."""
    return _limitador().conta(f"limite:{chave}", janela_segundos) <= maximo
