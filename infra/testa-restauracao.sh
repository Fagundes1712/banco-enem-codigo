#!/bin/bash
# Uso: testa-restauracao.sh <backup.dump.age> <arquivo da chave privada>. Restaura numa cópia descartável e confere as tabelas.
set -euo pipefail
raiz=$(cd "$(dirname "$0")/.." && pwd)
copia=restauracao-$$
trap 'docker rm -f "$copia" >/dev/null' EXIT

docker run -d --name "$copia" -e POSTGRES_PASSWORD=descartavel -e POSTGRES_DB=bancoenem postgres:17 >/dev/null
# Por TCP: durante a inicialização o PostgreSQL só escuta no socket local.
for _ in $(seq 60); do
  docker exec "$copia" pg_isready -q -h 127.0.0.1 -U postgres -d bancoenem && break
  sleep 1
done

# As políticas de RLS citam os papéis: eles precisam existir antes.
docker exec -i "$copia" psql -q -U postgres -d bancoenem -v ON_ERROR_STOP=1 -v senha_app=descartavel -v senha_migracao=descartavel -v senha_painel=descartavel <"$raiz/api/migracoes/papeis.sql"
age -d -i "$2" "$1" | docker exec -i "$copia" pg_restore -U postgres -d bancoenem --exit-on-error

consulta() { docker exec "$copia" psql -U postgres -d bancoenem -Atc "$1"; }
for tabela in usuarios sessoes tokens_email produtos pagamentos movimentos; do
  test "$(consulta "SELECT relrowsecurity AND relforcerowsecurity FROM pg_class WHERE oid = 'public.$tabela'::regclass")" = t
done
test -n "$(consulta 'SELECT version_num FROM alembic_version')"
echo "Restauração ok: $(consulta 'SELECT count(*) FROM usuarios') contas"
