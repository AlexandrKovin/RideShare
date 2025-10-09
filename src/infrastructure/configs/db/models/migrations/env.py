import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import (
    Connection,
    engine_from_config,
    pool,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from src.infrastructure.configs.config import config as app_config
from src.infrastructure.configs.db.models.base import metadata_obj

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def get_pg_uris_from_app_config() -> []:
    uris = []
    for pg_type in ['MASTER', 'SLAVE', 'URI']:
        if not hasattr(app_config.POSTGRES_CONFIG, pg_type):
            continue
        if pg_type == 'URI':
            uris.append(getattr(app_config.POSTGRES_CONFIG, pg_type))
        else:
            uris.append(getattr(getattr(app_config.POSTGRES_CONFIG, pg_type), 'URI'))
    return uris


for uri in get_pg_uris_from_app_config():
    config.set_main_option(f'{uri}.url', uri)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = metadata_obj
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    for url in get_pg_uris_from_app_config():
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={'paramstyle': 'named'},
        )

        with context.begin_transaction():
            context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    for url in get_pg_uris_from_app_config():
        connectable = AsyncEngine(
            engine_from_config(
                {
                    'sqlalchemy.url': url,
                },
                prefix='sqlalchemy.',
                poolclass=pool.NullPool,
                future=True,
            )
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
