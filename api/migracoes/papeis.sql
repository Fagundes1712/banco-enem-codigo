-- Roda uma vez, como administrador do banco, antes da primeira migração:
--   psql "$ADMIN_URL" -v ON_ERROR_STOP=1 -v senha_app="$SENHA_APP" -v senha_migracao="$SENHA_MIGRACAO" -v senha_painel="$SENHA_PAINEL" -f migracoes/papeis.sql
-- Pode rodar de novo: troca as senhas e confirma as permissões.

-- api_app: a API. Sujeita ao RLS; não cria nem altera tabela.
SELECT 'CREATE ROLE api_app' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_app') \gexec
ALTER ROLE api_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD :'senha_app';

-- api_migracao: só o deploy. Dona das tabelas.
SELECT 'CREATE ROLE api_migracao' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_migracao') \gexec
ALTER ROLE api_migracao LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD :'senha_migracao';

-- api_busca: ninguém entra com ele. É o dono das funções que acham o dono de um e-mail ou token.
SELECT 'CREATE ROLE api_busca' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_busca') \gexec
ALTER ROLE api_busca NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
GRANT api_busca TO api_migracao;

-- painel_leitura: o painel. Não lê tabela nenhuma; só executa as funções de totais.
SELECT 'CREATE ROLE painel_leitura' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'painel_leitura') \gexec
ALTER ROLE painel_leitura LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD :'senha_painel';

-- api_totais: ninguém entra com ele. É o dono das funções de totais e do contador de uso.
SELECT 'CREATE ROLE api_totais' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_totais') \gexec
ALTER ROLE api_totais NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
GRANT api_totais TO api_migracao;

ALTER SCHEMA public OWNER TO api_migracao;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
