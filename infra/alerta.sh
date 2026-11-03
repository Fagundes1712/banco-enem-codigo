#!/bin/bash
# Lê os eventos graves da API (app/auditoria.py) dos últimos 5 minutos e manda e-mail na hora.
. "$(dirname "$0")/comum.sh"
LIMITE_LOGIN=20 # senha errada é normal; só muitas juntas parecem ataque

registros=$(docker compose logs api --since 5m --no-log-prefix 2>&1)
conta() { grep -c "\"evento\": \"$1\"" <<<"$registros" || true; }

texto=""
for nome in renovacao_reusada webhook_recusado pagamento_divergente; do
  n=$(conta "$nome")
  if [ "$n" -gt 0 ]; then texto+="$nome: $n"$'\n'; fi
done
n=$(conta login_falhou)
if [ "$n" -ge "$LIMITE_LOGIN" ]; then texto+="login_falhou: $n"$'\n'; fi
if [ -n "$texto" ]; then avisa "Eventos de segurança nos últimos 5 minutos" "$texto"; fi
