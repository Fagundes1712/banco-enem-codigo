"""Direitos do titular (LGPD Art. 18): baixar meus dados e excluir minha conta."""

import logging
import secrets

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import delete, select

from .auth import Banco, _apaga_cookies, _revoga_todas, limita
from .db import Pagamento, Sessao, TokenEmail, Usuario
from .pagamentos import Logado
from .seguranca import confere_senha, gerar_hash

log = logging.getLogger("api")
router = APIRouter(prefix="/conta")


def _data(d):
    return d and d.isoformat()


@router.get("/dados")
def meus_dados(usuario: Logado, banco: Banco, resposta: Response):
    """Acesso e portabilidade (Art. 18, II e V): tudo o que guardamos sobre a pessoa, em JSON."""
    resposta.headers["Content-Disposition"] = 'attachment; filename="meus-dados-banco-enem.json"'
    sessoes = banco.scalars(select(Sessao).where(Sessao.usuario_id == usuario.id)).all()
    pagamentos = banco.scalars(select(Pagamento).where(Pagamento.usuario_id == usuario.id)).all()
    return {
        "conta": {
            "email": usuario.email,
            "criada_em": _data(usuario.criado_em),
            "email_confirmado": usuario.confirmado,
            "termos_versao": usuario.termos_versao,
            "termos_aceitos_em": _data(usuario.termos_aceitos_em),
            "assinatura_ate": _data(usuario.assinatura_ate),
        },
        "sessoes": [
            {"criada_em": _data(s.criada_em), "expira_em": _data(s.expira_em), "encerrada": s.revogada} for s in sessoes
        ],
        "pagamentos": [
            {
                "plano": p.plano,
                "valor_centavos": p.valor_centavos,
                "status": p.status,
                "criado_em": _data(p.criado_em),
                "pago_em": _data(p.pago_em),
            }
            for p in pagamentos
        ],
        "compartilhado_com": ["AbacatePay (pagamentos Pix)", "Resend (envio de e-mails)"],
    }


class Exclusao(BaseModel):
    senha: str


@router.post("/excluir")
def excluir_conta(dados: Exclusao, usuario: Logado, banco: Banco, resposta: Response):
    """Eliminação (Art. 18, VI). Pagamentos feitos ficam pelo prazo fiscal, sem e-mail nem senha."""
    limita(f"excluir:{usuario.id}", 5, 3600)
    if not confere_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(401, "Senha incorreta.")
    banco.execute(delete(Pagamento).where(Pagamento.usuario_id == usuario.id, Pagamento.status == "pendente"))
    banco.execute(delete(TokenEmail).where(TokenEmail.usuario_id == usuario.id))
    if banco.scalar(select(Pagamento.id).where(Pagamento.usuario_id == usuario.id).limit(1)):
        # Retenção legal (Art. 16, I): o registro do pagamento fica ligado a uma conta sem dados pessoais.
        _revoga_todas(banco, usuario.id)
        usuario.email = f"excluido-{usuario.id}@invalido"
        usuario.senha_hash = gerar_hash(secrets.token_urlsafe(32))
        usuario.confirmado = False
    else:
        banco.delete(usuario)
    banco.commit()
    log.info("conta %s excluída a pedido do titular", usuario.id)
    _apaga_cookies(resposta)
    return {"mensagem": "Conta excluída."}
