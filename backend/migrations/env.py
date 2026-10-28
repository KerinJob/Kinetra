from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.db import Base
from app import models  # noqa: F401
from app.config import get_settings

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

url = config.attributes.get("url") or get_settings().database_url


def run_migrations_online():
    engine = create_engine(url)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=Base.metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
