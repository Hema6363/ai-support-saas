from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy import pool

# Add backend directory to sys.path so app.* imports resolve cleanly
current_dir = os.path.dirname(__file__)
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.db.session import engine
from app.models.base import Base

# Import every model so Alembic can detect them
from app.models.tenant import Tenant
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.ticket import Ticket
from app.models.refresh_token import RefreshToken

config = context.config

config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()