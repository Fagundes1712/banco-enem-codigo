"""Rotas de conta: cadastro, confirmação, login, renovação, logout e recuperação de senha."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from . import servicos
from .config import config
from .db import Sessao, TokenEmail, Usuario, agora, sessao
from .seguranca import (
    ACESSO_SEGUNDOS,
    HASH_FALSO,
    confere_senha,
    emitir_acesso,
    gerar_hash,
    hash_token,
    ler_acesso,
    novo_token,
    senha_valida,
)

router = APIRouter(prefix="/auth")
Banco = Annotated[Session, Depends(sessao)]

TERMOS_VERSAO = "2026-10"
RENOVACAO_DIAS = 30
PRAZO = {"confirmar": timedelta(hours=24), "senha": timedelta(minutes=30)}


def ip_do_cliente(request: Request) -> str:
    # Em produção a API só recebe tráfego do Cloudflare, que informa o IP real neste cabeçalho.
    if config().producao and request.headers.get("cf-connecting-ip"):
        return request.headers["cf-connecting-ip"]
    return request.client.host if request.client else "?"


def limita(chave: str, maximo: int, janela: int) -> None:
    if not servicos.permite(chave, maximo, janela):
        raise HTTPException(429, "Muitas tentativas. Espere alguns minutos e tente de novo.")


def exige_turnstile(token: str, request: Request) -> None:
    if not servicos.verifica_turnstile(token, ip_do_cliente(request)):
        raise HTTPException(400, "Confirme que você não é um robô.")


def usuario_atual(banco: Banco, acesso: Annotated[str | None, Cookie()] = None) -> Usuario:
    usuario_id = ler_acesso(acesso) if acesso else None
    usuario = banco.get(Usuario, usuario_id) if usuario_id else None
    if not usuario:
        raise HTTPException(401, "Entre na sua conta.")
    return usuario


def _grava_cookies(resposta: Response, acesso: str, renovacao: str) -> None:
    c = config()
    comum = {"httponly": True, "secure": c.producao, "samesite": "strict", "domain": c.cookie_domain}
    resposta.set_cookie("acesso", acesso, max_age=ACESSO_SEGUNDOS, path="/", **comum)
    resposta.set_cookie("renovacao", renovacao, max_age=RENOVACAO_DIAS * 86400, path="/auth", **comum)


def _apaga_cookies(resposta: Response) -> None:
    c = config()
    comum = {"httponly": True, "secure": c.producao, "samesite": "strict", "domain": c.cookie_domain}
    resposta.delete_cookie("acesso", path="/", **comum)
    resposta.delete_cookie("renovacao", path="/auth", **comum)


def _abre_sessao(banco: Session, usuario_id: str, resposta: Response) -> None:
    token, h = novo_token()
    banco.add(Sessao(usuario_id=usuario_id, token_hash=h, expira_em=agora() + timedelta(days=RENOVACAO_DIAS)))
    banco.commit()
    _grava_cookies(resposta, emitir_acesso(usuario_id), token)


def _revoga_todas(banco: Session, usuario_id: str) -> None:
    banco.execute(update(Sessao).where(Sessao.usuario_id == usuario_id).values(revogada=True))


def _envia_link(banco: Session, usuario: Usuario, tipo: str, fila: BackgroundTasks) -> None:
    # O e-mail sai depois da resposta: o tempo dela não revela se a conta existe.
    token, h = novo_token()
    banco.add(TokenEmail(usuario_id=usuario.id, tipo=tipo, token_hash=h, expira_em=agora() + PRAZO[tipo]))
    banco.commit()
    site = config().site_url
    if tipo == "confirmar":
        fila.add_task(
            servicos.envia_email,
            usuario.email,
            "Confirme seu e-mail no Banco ENEM",
            f"Para ativar sua conta, abra este link em até 24 horas:\n{site}/?confirmar={token}",
        )
    else:
        fila.add_task(
            servicos.envia_email,
            usuario.email,
            "Trocar a senha do Banco ENEM",
            f"Para criar uma senha nova, abra este link em até 30 minutos:\n{site}/?nova-senha={token}\n\n"
            "Se não foi você, ignore este e-mail.",
        )


def _usa_token(banco: Session, token: str, tipo: str) -> Usuario:
    """Marca o token como usado (uma vez só) e devolve o dono."""
    linha = banco.execute(
        update(TokenEmail)
        .where(
            TokenEmail.token_hash == hash_token(token),
            TokenEmail.tipo == tipo,
            TokenEmail.usado.is_(False),
            TokenEmail.expira_em > agora(),
        )
        .values(usado=True)
        .returning(TokenEmail.usuario_id)
    ).first()
    if not linha:
        raise HTTPException(400, "Link inválido ou vencido. Peça um novo.")
    return banco.get(Usuario, linha.usuario_id)


class Cadastro(BaseModel):
    email: EmailStr
    senha: str
    turnstile: str
    aceite_termos: bool


class Login(BaseModel):
    email: EmailStr
    senha: str
    turnstile: str


class Token(BaseModel):
    token: str


class Esqueci(BaseModel):
    email: EmailStr
    turnstile: str


class NovaSenha(BaseModel):
    token: str
    senha: str


RESPOSTA_CADASTRO = {"mensagem": "Se o e-mail puder ser usado, enviamos um link de confirmação."}


@router.post("/cadastro", status_code=202)
def cadastro(dados: Cadastro, request: Request, banco: Banco, fila: BackgroundTasks):
    limita(f"cadastro:{ip_do_cliente(request)}", 5, 3600)
    exige_turnstile(dados.turnstile, request)
    if not dados.aceite_termos:
        raise HTTPException(400, "Aceite os termos de uso e a política de privacidade.")
    if not senha_valida(dados.senha):
        raise HTTPException(400, "A senha precisa ter de 8 a 72 caracteres (acentos contam em dobro).")
    email = dados.email.lower()
    senha_hash = gerar_hash(dados.senha)  # antes da busca: mesmo tempo de resposta com ou sem conta
    if banco.scalar(select(Usuario).where(Usuario.email == email)):
        # Mesma resposta para não revelar quem tem conta.
        return RESPOSTA_CADASTRO
    usuario = Usuario(email=email, senha_hash=senha_hash, termos_versao=TERMOS_VERSAO)
    banco.add(usuario)
    banco.commit()
    _envia_link(banco, usuario, "confirmar", fila)
    return RESPOSTA_CADASTRO


@router.post("/confirmar")
def confirmar(dados: Token, banco: Banco):
    usuario = _usa_token(banco, dados.token, "confirmar")
    usuario.confirmado = True
    banco.commit()
    return {"mensagem": "E-mail confirmado. Agora é só entrar."}


@router.post("/login")
def login(dados: Login, request: Request, resposta: Response, banco: Banco):
    email = dados.email.lower()
    limita(f"login-ip:{ip_do_cliente(request)}", 20, 600)
    limita(f"login-email:{email}", 5, 900)
    exige_turnstile(dados.turnstile, request)
    usuario = banco.scalar(select(Usuario).where(Usuario.email == email))
    if not confere_senha(dados.senha, usuario.senha_hash if usuario else HASH_FALSO) or not usuario:
        raise HTTPException(401, "E-mail ou senha incorretos.")
    if not usuario.confirmado:
        raise HTTPException(403, "Confirme seu e-mail antes de entrar.")
    _abre_sessao(banco, usuario.id, resposta)
    return {"mensagem": "ok"}


@router.post("/refresh")
def refresh(resposta: Response, banco: Banco, renovacao: Annotated[str | None, Cookie()] = None):
    atual = banco.scalar(select(Sessao).where(Sessao.token_hash == hash_token(renovacao))) if renovacao else None
    if not atual or atual.expira_em <= agora():
        _apaga_cookies(resposta)
        raise HTTPException(401, "Sessão vencida. Entre de novo.")
    # Só quem troca o token de não revogado para revogado ganha um novo: dois usos do mesmo token = roubo.
    trocou = banco.execute(
        update(Sessao).where(Sessao.id == atual.id, Sessao.revogada.is_(False)).values(revogada=True)
    ).rowcount
    if not trocou:
        _revoga_todas(banco, atual.usuario_id)
        banco.commit()
        _apaga_cookies(resposta)
        raise HTTPException(401, "Sessão encerrada por segurança. Entre de novo.")
    _abre_sessao(banco, atual.usuario_id, resposta)
    return {"mensagem": "ok"}


@router.post("/logout")
def logout(resposta: Response, banco: Banco, renovacao: Annotated[str | None, Cookie()] = None):
    if renovacao:
        banco.execute(update(Sessao).where(Sessao.token_hash == hash_token(renovacao)).values(revogada=True))
        banco.commit()
    _apaga_cookies(resposta)
    return {"mensagem": "ok"}


@router.post("/esqueci", status_code=202)
def esqueci(dados: Esqueci, request: Request, banco: Banco, fila: BackgroundTasks):
    email = dados.email.lower()
    limita(f"esqueci-ip:{ip_do_cliente(request)}", 5, 3600)
    limita(f"esqueci-email:{email}", 3, 3600)
    exige_turnstile(dados.turnstile, request)
    usuario = banco.scalar(select(Usuario).where(Usuario.email == email))
    if usuario:
        _envia_link(banco, usuario, "senha", fila)
    return {"mensagem": "Se houver uma conta com esse e-mail, enviamos um link."}


@router.post("/nova-senha")
def nova_senha(dados: NovaSenha, request: Request, banco: Banco):
    limita(f"nova-senha:{ip_do_cliente(request)}", 10, 3600)
    if not senha_valida(dados.senha):
        raise HTTPException(400, "A senha precisa ter de 8 a 72 caracteres (acentos contam em dobro).")
    usuario = _usa_token(banco, dados.token, "senha")
    usuario.senha_hash = gerar_hash(dados.senha)
    usuario.confirmado = True  # quem recebeu o link prova que é dono do e-mail
    _revoga_todas(banco, usuario.id)
    # Outros links de troca pedidos antes deixam de valer.
    banco.execute(update(TokenEmail).where(TokenEmail.usuario_id == usuario.id, TokenEmail.tipo == "senha").values(usado=True))
    banco.commit()
    return {"mensagem": "Senha trocada. Entre com a senha nova."}
