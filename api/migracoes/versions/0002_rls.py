"""RLS forçado em todas as tabelas, permissões do api_app e funções de busca do dono"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# Tabela e a coluna que diz de quem é a linha.
DO_USUARIO = {
    "usuarios": "id",
    "sessoes": "usuario_id",
    "tokens_email": "usuario_id",
    "pagamentos": "usuario_id",
    "movimentos": "usuario_id",
}

# Função, tabela, coluna devolvida e coluna procurada. Cada uma devolve só o id do dono.
BUSCAS = {
    "conta_por_email": ("usuarios", "id", "email"),
    "dono_token_email": ("tokens_email", "usuario_id", "token_hash"),
    "dono_sessao": ("sessoes", "usuario_id", "token_hash"),
    "dono_checkout": ("pagamentos", "usuario_id", "checkout_id"),
}


def upgrade() -> None:
    op.execute("GRANT USAGE ON SCHEMA public TO api_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON usuarios, sessoes, tokens_email, pagamentos, produtos TO api_app")
    # Trilha só de inclusão: sem UPDATE nem DELETE.
    op.execute("GRANT SELECT, INSERT ON movimentos TO api_app")

    for tabela, coluna in DO_USUARIO.items():
        op.execute(f"ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY")
        regra = f"{coluna} = current_setting('app.usuario_id', true)"
        op.execute(f"CREATE POLICY so_o_dono ON {tabela} TO api_app USING ({regra}) WITH CHECK ({regra})")

    # Produtos são os planos à venda: não têm dono, mas seguem com RLS ligado como todas as outras.
    op.execute("ALTER TABLE produtos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE produtos FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY todos ON produtos TO api_app USING (true) WITH CHECK (true)")

    # O dono de uma função precisa de CREATE no schema só no momento da troca.
    op.execute("GRANT USAGE, CREATE ON SCHEMA public TO api_busca")
    for funcao, (tabela, devolve, procura) in BUSCAS.items():
        op.execute(f"GRANT SELECT ({devolve}, {procura}) ON {tabela} TO api_busca")
        op.execute(f"CREATE POLICY busca ON {tabela} FOR SELECT TO api_busca USING (true)")
        op.execute(
            f"CREATE FUNCTION {funcao}(valor text) RETURNS text LANGUAGE sql STABLE SECURITY DEFINER "
            f"SET search_path = public, pg_temp AS $$ SELECT {devolve} FROM {tabela} WHERE {procura} = valor $$"
        )
        op.execute(f"ALTER FUNCTION {funcao}(text) OWNER TO api_busca")
        op.execute(f"REVOKE ALL ON FUNCTION {funcao}(text) FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {funcao}(text) TO api_app")
    op.execute("REVOKE CREATE ON SCHEMA public FROM api_busca")


def downgrade() -> None:
    for funcao, (tabela, _devolve, _procura) in BUSCAS.items():
        op.execute(f"DROP FUNCTION {funcao}(text)")
        op.execute(f"DROP POLICY busca ON {tabela}")
        op.execute(f"REVOKE ALL ON {tabela} FROM api_busca")
    op.execute("REVOKE ALL ON SCHEMA public FROM api_busca")
    op.execute("DROP POLICY todos ON produtos")
    op.execute("ALTER TABLE produtos NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE produtos DISABLE ROW LEVEL SECURITY")
    for tabela in DO_USUARIO:
        op.execute(f"DROP POLICY so_o_dono ON {tabela}")
        op.execute(f"ALTER TABLE {tabela} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON usuarios, sessoes, tokens_email, pagamentos, produtos, movimentos FROM api_app")
    op.execute("REVOKE ALL ON SCHEMA public FROM api_app")
