#!/bin/bash
# Backup diário: criptografa antes de sair da máquina. Só a chave pública fica aqui; a privada fica fora do servidor.
. "$(dirname "$0")/comum.sh"
trap 'avisa "Backup falhou" "Veja: journalctl -u banco-enem-backup"' ERR
arquivo=$(mktemp)
trap 'rm -f "$arquivo"' EXIT

docker compose exec -T postgres pg_dump -U postgres -Fc bancoenem | age -r "$BACKUP_CHAVE_PUBLICA" >"$arquivo"
test -s "$arquivo"
rclone copyto "$arquivo" "$BACKUP_DESTINO/bancoenem-$(date -u +%F).dump.age"
rclone delete --min-age 30d "$BACKUP_DESTINO"
