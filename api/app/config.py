"""Configuração lida das variáveis de ambiente (ver api/.env.example)."""

import os
from dataclasses import dataclass
from functools import lru_cache


def _env(nome: str, padrao: str | None = None) -> str:
    valor = os.environ.get(nome, padrao)
    if valor is None or valor == "":
        # O erro cita o nome, nunca o valor.
        raise RuntimeError(f"Variável de ambiente ausente: {nome} (ver api/.env.example)")
    return valor


@dataclass(frozen=True)
class Config:
    ambiente: str  # dev, teste ou producao
    database_url: str
    redis_url: str
    jwt_secret: str
    site_url: str
    cookie_domain: str | None
    turnstile_secret: str
    resend_api_key: str
    email_remetente: str
    abacatepay_api_key: str
    abacatepay_webhook_secret: str
    abacatepay_dev_mode: bool

    @property
    def producao(self) -> bool:
        return self.ambiente == "producao"


@lru_cache
def config() -> Config:
    ambiente = _env("AMBIENTE", "dev")
    if ambiente not in ("dev", "teste", "producao"):
        raise RuntimeError("AMBIENTE deve ser dev, teste ou producao")
    producao = ambiente == "producao"
    c = Config(
        ambiente=ambiente,
        database_url=_env("DATABASE_URL"),
        # Sem Redis o limite de tentativas fica na memória de cada instância: só serve fora de produção.
        redis_url=_env("REDIS_URL") if producao else os.environ.get("REDIS_URL", ""),
        jwt_secret=_env("JWT_SECRET"),
        site_url=_env("SITE_URL").rstrip("/"),
        cookie_domain=os.environ.get("COOKIE_DOMAIN") or None,
        turnstile_secret=_env("TURNSTILE_SECRET"),
        resend_api_key=_env("RESEND_API_KEY") if producao else os.environ.get("RESEND_API_KEY", ""),
        email_remetente=_env("EMAIL_REMETENTE", "Banco ENEM <nao-responda@localhost>"),
        abacatepay_api_key=_env("ABACATEPAY_API_KEY"),
        abacatepay_webhook_secret=_env("ABACATEPAY_WEBHOOK_SECRET"),
        abacatepay_dev_mode=_env("ABACATEPAY_DEV_MODE", "true") == "true",
    )
    if len(c.jwt_secret) < 32 or len(c.abacatepay_webhook_secret) < 16:
        raise RuntimeError("JWT_SECRET precisa de 32+ caracteres e ABACATEPAY_WEBHOOK_SECRET de 16+")
    if producao and (c.abacatepay_dev_mode or not c.site_url.startswith("https://")):
        raise RuntimeError("Em produção: ABACATEPAY_DEV_MODE=false e SITE_URL com https")
    return c
