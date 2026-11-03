"""Tabelas iniciais"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("senha_hash", sa.String(60), nullable=False),
        sa.Column("confirmado", sa.Boolean(), nullable=False),
        sa.Column("termos_versao", sa.String(20), nullable=False),
        sa.Column("termos_aceitos_em", sa.DateTime(), nullable=False),
        sa.Column("assinatura_ate", sa.DateTime(), nullable=True),
        sa.Column("senha_trocada_em", sa.DateTime(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "sessoes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("usuario_id", sa.String(36), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expira_em", sa.DateTime(), nullable=False),
        sa.Column("revogada", sa.Boolean(), nullable=False),
        sa.Column("criada_em", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sessoes_usuario_id", "sessoes", ["usuario_id"])
    op.create_table(
        "tokens_email",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("usuario_id", sa.String(36), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expira_em", sa.DateTime(), nullable=False),
        sa.Column("usado", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_tokens_email_usuario_id", "tokens_email", ["usuario_id"])
    op.create_table(
        "produtos",
        sa.Column("plano", sa.String(20), primary_key=True),
        sa.Column("abacatepay_id", sa.String(100), nullable=False, unique=True),
        sa.Column("valor_centavos", sa.Integer(), nullable=False),
    )
    op.create_table(
        "pagamentos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("usuario_id", sa.String(36), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plano", sa.String(20), nullable=False),
        sa.Column("checkout_id", sa.String(100), nullable=False, unique=True),
        sa.Column("valor_centavos", sa.Integer(), nullable=False),
        sa.Column("dias", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("pago_em", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_pagamentos_usuario_id", "pagamentos", ["usuario_id"])
    op.create_table(
        "movimentos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("usuario_id", sa.String(36), nullable=False),
        sa.Column("pagamento_id", sa.String(36), nullable=False),
        sa.Column("evento", sa.String(10), nullable=False),
        sa.Column("valor_centavos", sa.Integer(), nullable=False),
        sa.Column("em", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_movimentos_usuario_id", "movimentos", ["usuario_id"])


def downgrade() -> None:
    for tabela in ("movimentos", "pagamentos", "produtos", "tokens_email", "sessoes", "usuarios"):
        op.drop_table(tabela)
