"""Senhas (bcrypt), tokens de acesso (JWT) e tokens aleatórios de uso único."""

import hashlib
import secrets
import time

import bcrypt
import jwt

from .config import config

CUSTO_BCRYPT = 12
ACESSO_SEGUNDOS = 15 * 60
EMISSOR = "api.bancoenem"
PUBLICO = "bancoenem"

# Hash de uma senha que ninguém conhece: o login de um e-mail inexistente roda o bcrypt
# contra ele, e a resposta demora o mesmo tempo que a de um e-mail cadastrado.
HASH_FALSO = bcrypt.hashpw(secrets.token_bytes(16), bcrypt.gensalt(CUSTO_BCRYPT)).decode()


def senha_valida(senha: str) -> bool:
    # bcrypt só usa os primeiros 72 bytes; acima disso recusamos em vez de cortar.
    return len(senha) >= 8 and len(senha.encode("utf-8")) <= 72


def gerar_hash(senha: str) -> str:
    if not senha_valida(senha):
        raise ValueError("senha inválida")
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(CUSTO_BCRYPT)).decode()


def confere_senha(senha: str, hash_salvo: str) -> bool:
    if not senha_valida(senha):
        return False
    return bcrypt.checkpw(senha.encode("utf-8"), hash_salvo.encode())


def emitir_acesso(usuario_id: str) -> str:
    t = int(time.time())
    dados = {"sub": usuario_id, "iat": t, "exp": t + ACESSO_SEGUNDOS, "iss": EMISSOR, "aud": PUBLICO}
    return jwt.encode(dados, config().jwt_secret, algorithm="HS256")


def ler_acesso(token: str) -> dict | None:
    """Devolve os dados do token (sub, iat, exp) ou None se for inválido ou vencido."""
    try:
        dados = jwt.decode(
            token,
            config().jwt_secret,
            algorithms=["HS256"],  # fixo: nunca aceitar o algoritmo que vem no token
            issuer=EMISSOR,
            audience=PUBLICO,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError:
        return None
    return dados


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def novo_token() -> tuple[str, str]:
    """Token aleatório de 32 bytes e o hash que vai para o banco."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)
