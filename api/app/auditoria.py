"""Registro de eventos de segurança: uma linha JSON por evento, para achar abuso nos logs do Cloud Run.

Só o id interno da conta: nada de e-mail, senha, token ou IP (o IP fica nos logs do Cloudflare).
"""

import json
import logging

log = logging.getLogger("auditoria")

# Eventos que pedem atenção de quem cuida do sistema saem como WARNING (dá para criar alerta por nível).
GRAVES = {"login_falhou", "renovacao_reusada", "webhook_recusado", "pagamento_divergente"}


def evento(nome: str, usuario_id: str | None = None, **extra: str | int) -> None:
    linha = json.dumps({"evento": nome, "usuario": usuario_id, **extra}, ensure_ascii=False)
    log.log(logging.WARNING if nome in GRAVES else logging.INFO, linha)
