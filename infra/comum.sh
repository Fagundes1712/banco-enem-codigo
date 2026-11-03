#!/bin/bash
# Carregado pelos outros scripts: entra em infra/, lê o .env e define avisa.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
set -a
# shellcheck disable=SC1091
. ./.env
set +a

# Falha no e-mail não pode derrubar o script: o texto também fica no journal.
avisa() {
  echo "aviso: $1: $2" >&2
  python3 -c 'import json,os,sys; print(json.dumps({"from": os.environ["EMAIL_REMETENTE"], "to": os.environ["ALERTA_EMAIL"], "subject": "[Banco ENEM] " + sys.argv[1], "text": sys.argv[2]}))' "$1" "$2" |
    curl -fsS --max-time 20 https://api.resend.com/emails -H "Authorization: Bearer $RESEND_API_KEY" -H "Content-Type: application/json" -d @- >/dev/null ||
    echo "aviso: e-mail não saiu" >&2
}
