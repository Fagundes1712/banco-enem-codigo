"""Planos, checkout Pix na AbacatePay, webhook e liberação da assinatura."""

import json
import logging
import uuid
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from . import abacatepay
from . import auditoria
from .auth import Banco, limita, usuario_atual
from .config import config
from .db import Pagamento, Produto, Usuario, agora, sessao

log = logging.getLogger("api")


def _linha(x) -> str:
    """Valor vindo de fora vira uma linha só no log: ninguém forja uma entrada nova com quebra de linha."""
    return str(x).replace("\r", " ").replace("\n", " ")


router = APIRouter()

# O preço vale daqui, nunca do navegador nem do webhook.
PLANOS = {
    "mensal": {"nome": "Banco ENEM - assinatura mensal", "centavos": 2499, "dias": 30},
    "anual": {"nome": "Banco ENEM - assinatura anual", "centavos": 23988, "dias": 365},
}

Logado = Annotated[Usuario, Depends(usuario_atual)]


def assinatura_ativa(usuario: Usuario) -> bool:
    return usuario.assinatura_ate is not None and usuario.assinatura_ate > agora()


@router.get("/planos")
def planos():
    return [{"id": k, "centavos": p["centavos"], "dias": p["dias"]} for k, p in PLANOS.items()]


@router.get("/me")
def me(usuario: Logado):
    ate = usuario.assinatura_ate
    return {"email": usuario.email, "assinatura_ativa": assinatura_ativa(usuario), "assinatura_ate": ate and ate.isoformat()}


def _produto(banco: Session, plano: str) -> str:
    p = PLANOS[plano]
    existente = banco.get(Produto, plano)
    if existente and existente.valor_centavos == p["centavos"]:
        return existente.abacatepay_id
    # Preço novo = produto novo na AbacatePay (o id externo leva o preço para não colidir).
    produto_id = abacatepay.cria_produto(f"bancoenem-{plano}-{p['centavos']}", p["nome"], p["centavos"])
    banco.merge(Produto(plano=plano, abacatepay_id=produto_id, valor_centavos=p["centavos"]))
    banco.commit()
    return produto_id


class NovoPagamento(BaseModel):
    plano: Literal["mensal", "anual"]


@router.post("/pagamentos")
def novo_pagamento(dados: NovoPagamento, usuario: Logado, banco: Banco):
    limita(f"pagamento:{usuario.id}", 10, 3600)
    if not usuario.confirmado:
        raise HTTPException(403, "Confirme seu e-mail antes de assinar.")
    p = PLANOS[dados.plano]
    pagamento = Pagamento(id=str(uuid.uuid4()), usuario_id=usuario.id, plano=dados.plano, valor_centavos=p["centavos"], dias=p["dias"])
    try:
        checkout = abacatepay.cria_checkout(_produto(banco, dados.plano), pagamento.id, config().site_url + "/?pagamento=1")
    except abacatepay.AbacatePayErro:
        raise HTTPException(502, "O pagamento está indisponível agora. Tente de novo em instantes.") from None
    if checkout["amount"] != p["centavos"]:
        log.error("Preço na AbacatePay (%s) difere do plano %s (%s)", _linha(checkout["amount"]), _linha(dados.plano), p["centavos"])
        raise HTTPException(502, "O pagamento está indisponível agora.")
    pagamento.checkout_id = checkout["id"]
    banco.add(pagamento)
    banco.commit()
    return {"url": checkout["url"]}


def sincroniza(banco: Session, checkout_id: str) -> str:
    """Pergunta à AbacatePay se o checkout foi pago e libera os dias uma vez só."""
    conhecido = banco.scalar(select(Pagamento.status).where(Pagamento.checkout_id == checkout_id))
    if conhecido is None:
        return "desconhecido"
    if conhecido == "pago":
        return "ja_processado"
    checkout = abacatepay.consulta_checkout(checkout_id)
    if checkout["status"] != "PAID":
        return "nao_pago"
    pago = checkout["paidAmount"] if checkout["paidAmount"] is not None else checkout["amount"]
    # Só a chamada que muda de pendente para pago (com o valor certo) libera os dias.
    linha = banco.execute(
        update(Pagamento)
        .where(Pagamento.checkout_id == checkout_id, Pagamento.status == "pendente", Pagamento.valor_centavos == pago)
        .values(status="pago", pago_em=agora())
        .returning(Pagamento.usuario_id, Pagamento.dias)
    ).first()
    if not linha:
        banco.rollback()
        atual = banco.scalar(select(Pagamento.status).where(Pagamento.checkout_id == checkout_id))
        if atual == "pago":
            return "ja_processado"
        auditoria.evento("pagamento_divergente", checkout=checkout_id, pago=pago)
        return "valor_divergente"
    usuario = banco.scalar(select(Usuario).where(Usuario.id == linha.usuario_id).with_for_update())
    inicio = max(usuario.assinatura_ate or agora(), agora())  # renovação antes de vencer soma os dias
    usuario.assinatura_ate = inicio + timedelta(days=linha.dias)
    banco.commit()
    auditoria.evento("assinatura_liberada", linha.usuario_id, dias=linha.dias)
    return "liberado"


@router.post("/pagamentos/sincronizar")
def sincronizar(usuario: Logado, banco: Banco):
    """Chamado quando o aluno volta da página de pagamento: não depende do webhook chegar."""
    limita(f"sincronizar:{usuario.id}", 30, 3600)
    pendentes = banco.scalars(
        select(Pagamento.checkout_id)
        .where(Pagamento.usuario_id == usuario.id, Pagamento.status == "pendente")
        .order_by(Pagamento.criado_em.desc())
        .limit(5)
    ).all()
    for checkout_id in pendentes:
        try:
            sincroniza(banco, checkout_id)
        except abacatepay.AbacatePayErro:
            log.warning("Não deu para conferir o checkout %s agora", checkout_id)
    banco.refresh(usuario)
    return {"assinatura_ativa": assinatura_ativa(usuario)}


@router.post("/webhooks/abacatepay")
async def webhook(request: Request, banco: Annotated[Session, Depends(sessao)]):
    # Cadastre na AbacatePay: https://<api>/webhooks/abacatepay?webhookSecret=<ABACATEPAY_WEBHOOK_SECRET>
    corpo = await request.body()
    segredo = request.query_params.get("webhookSecret", "")
    if not abacatepay.webhook_autentico(segredo, request.headers.get("x-webhook-signature", ""), corpo):
        auditoria.evento("webhook_recusado")
        raise HTTPException(401, "não autorizado")
    try:
        evento = json.loads(corpo)
        checkout_id = (evento.get("data") or {}).get("checkout", {}).get("id")
        dev_mode = evento.get("devMode")
    except (ValueError, AttributeError):
        raise HTTPException(400, "evento inválido") from None
    if evento.get("event") != "checkout.completed" or not isinstance(checkout_id, str) or not checkout_id:
        return {"recebido": True}
    # Pagamento de teste nunca libera produção, e vice-versa.
    if dev_mode is not config().abacatepay_dev_mode:
        return {"recebido": True}
    try:
        log.info("checkout %s: %s", _linha(checkout_id), sincroniza(banco, checkout_id))
    except abacatepay.AbacatePayErro as e:
        # 4xx (fora 429) = a AbacatePay não conhece o checkout: repetir não ajuda.
        if e.status and 400 <= e.status < 500 and e.status != 429:
            return {"recebido": True}
        raise HTTPException(503, "tente mais tarde") from None
    return {"recebido": True}
