"""Contador de uso e funções de totais do painel, sem acesso do painel às tabelas"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

ATIVA = "x.assinatura_ate > (now() AT TIME ZONE 'utc')"

# Assinatura e corpo. Nenhuma devolve e-mail: o api_totais nem tem permissão na coluna.
FUNCOES = {
    "painel_contas(periodo text)": (
        "TABLE (inicio date, total bigint)",
        "SELECT date_trunc(periodo, criado_em)::date, count(*) FROM usuarios WHERE confirmado GROUP BY 1 ORDER BY 1",
    ),
    "painel_faturamento(periodo text)": (
        "TABLE (inicio date, pagamentos bigint, centavos bigint)",
        "SELECT date_trunc(periodo, pago_em)::date, count(*), sum(valor_centavos)::bigint FROM pagamentos "
        "WHERE status = 'pago' GROUP BY 1 ORDER BY 1",
    ),
    "painel_uso(periodo text)": (
        "TABLE (inicio date, plano text, questoes bigint, minutos bigint)",
        "SELECT date_trunc(periodo, dia)::date, plano::text, sum(questoes)::bigint, sum(minutos)::bigint FROM uso_diario "
        "GROUP BY 1, 2 ORDER BY 1, 2",
    ),
    "painel_assinantes()": (
        "TABLE (plano text, ativos bigint, nao_renovaram bigint)",
        "WITH ultimo AS (SELECT DISTINCT ON (usuario_id) usuario_id, plano FROM pagamentos WHERE status = 'pago' "
        "ORDER BY usuario_id, pago_em DESC) "
        f"SELECT u.plano::text, count(*) FILTER (WHERE {ATIVA}), count(*) FILTER (WHERE NOT coalesce({ATIVA}, false)) "
        "FROM ultimo u JOIN usuarios x ON x.id = u.usuario_id WHERE x.confirmado GROUP BY 1 ORDER BY 1",
    ),
    "painel_conversao()": (
        "TABLE (contas bigint, assinantes bigint)",
        "SELECT (SELECT count(*) FROM usuarios WHERE confirmado), "
        "(SELECT count(DISTINCT p.usuario_id) FROM pagamentos p JOIN usuarios x ON x.id = p.usuario_id "
        "WHERE p.status = 'pago' AND x.confirmado)",
    ),
}


def upgrade() -> None:
    op.create_table(
        "uso_diario",
        sa.Column("dia", sa.Date(), primary_key=True),
        sa.Column("plano", sa.String(10), primary_key=True),
        sa.Column("questoes", sa.Integer(), nullable=False),
        sa.Column("minutos", sa.Integer(), nullable=False),
    )
    op.execute("ALTER TABLE uso_diario ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE uso_diario FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY totais ON uso_diario TO api_totais USING (true) WITH CHECK (true)")
    op.execute("GRANT SELECT, INSERT, UPDATE ON uso_diario TO api_totais")

    op.execute("GRANT SELECT (id, confirmado, criado_em, assinatura_ate) ON usuarios TO api_totais")
    op.execute("GRANT SELECT (usuario_id, plano, status, valor_centavos, pago_em) ON pagamentos TO api_totais")
    for tabela in ("usuarios", "pagamentos"):
        op.execute(f"CREATE POLICY totais ON {tabela} FOR SELECT TO api_totais USING (true)")

    op.execute("GRANT USAGE ON SCHEMA public TO painel_leitura")
    # O dono de uma função precisa de CREATE no schema só no momento da troca.
    op.execute("GRANT USAGE, CREATE ON SCHEMA public TO api_totais")
    seguranca = "SECURITY DEFINER SET search_path = public, pg_temp"
    for assinatura, (devolve, corpo) in FUNCOES.items():
        tipos = assinatura.replace("periodo ", "")
        op.execute(f"CREATE FUNCTION {assinatura} RETURNS {devolve} LANGUAGE sql STABLE {seguranca} AS $$ {corpo} $$")
        op.execute(f"ALTER FUNCTION {tipos} OWNER TO api_totais")
        op.execute(f"REVOKE ALL ON FUNCTION {tipos} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {tipos} TO painel_leitura")

    op.execute(
        f"CREATE FUNCTION soma_uso(p_plano text, p_questoes int, p_minutos int) RETURNS void LANGUAGE sql {seguranca} AS $$ "
        "INSERT INTO uso_diario (dia, plano, questoes, minutos) "
        "VALUES ((now() AT TIME ZONE 'utc')::date, p_plano, p_questoes, p_minutos) "
        "ON CONFLICT (dia, plano) DO UPDATE SET questoes = uso_diario.questoes + excluded.questoes, "
        "minutos = uso_diario.minutos + excluded.minutos $$"
    )
    op.execute("ALTER FUNCTION soma_uso(text, int, int) OWNER TO api_totais")
    op.execute("REVOKE ALL ON FUNCTION soma_uso(text, int, int) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION soma_uso(text, int, int) TO api_app")
    op.execute("REVOKE CREATE ON SCHEMA public FROM api_totais")


def downgrade() -> None:
    op.execute("DROP FUNCTION soma_uso(text, int, int)")
    for assinatura in FUNCOES:
        op.execute(f"DROP FUNCTION {assinatura.replace('periodo ', '')}")
    for tabela in ("usuarios", "pagamentos"):
        op.execute(f"DROP POLICY totais ON {tabela}")
        op.execute(f"REVOKE ALL ON {tabela} FROM api_totais")
    op.drop_table("uso_diario")
    op.execute("REVOKE ALL ON SCHEMA public FROM api_totais")
    op.execute("REVOKE ALL ON SCHEMA public FROM painel_leitura")
