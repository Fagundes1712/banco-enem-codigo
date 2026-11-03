#!/bin/bash
# Roda de tempos em tempos: se o branch api-producao andou (CI verde na main ou volta de versão), sobe a versão nova.
# O servidor busca a versão: nenhuma porta aberta e nenhuma chave da máquina no GitHub.
. "$(dirname "$0")/comum.sh"
git fetch -q origin api-producao
novo=$(git rev-parse FETCH_HEAD)
[ "$novo" = "$(git rev-parse HEAD)" ] && exit 0

trap 'avisa "Atualização falhou" "Versão $novo não subiu. Veja: journalctl -u banco-enem-atualiza"' ERR
git checkout -q --detach "$novo"
docker compose pull -q postgres redis
docker compose up -d --build
curl -fsS --retry 20 --retry-connrefused --retry-all-errors --retry-delay 3 -H "X-Origem: $ORIGEM_SECRET" http://127.0.0.1:8080/saude >/dev/null
echo "Atualizado para $novo"
