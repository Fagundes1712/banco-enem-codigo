"""Migrações com o papel api_migracao. A API roda com api_app e não consegue alterar tabelas."""

import os

from alembic import context
from sqlalchemy import create_engine

from app.db import Base

url = os.environ.get("MIGRACAO_DATABASE_URL")
if not url:
    raise RuntimeError("Variável de ambiente ausente: MIGRACAO_DATABASE_URL (ver api/.env.example)")

if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(url).connect() as conexao:
        context.configure(connection=conexao, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
