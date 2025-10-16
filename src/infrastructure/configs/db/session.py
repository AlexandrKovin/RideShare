from typing import AsyncGenerator

from sqlalchemy import (
    Delete,
    Update,
)
from sqlalchemy.dialects.mysql import Insert
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session

from src.infrastructure.configs.config import config


def create_engines() -> dict[str, AsyncEngine]:
    result = {}

    if hasattr(config.POSTGRES_CONFIG, 'URI'):
        result['single_node'] = create_async_engine(
            config.POSTGRES_CONFIG.URI, pool_recycle=3600
        )
    elif hasattr(config.POSTGRES_CONFIG, 'MASTER') and hasattr(
        config.POSTGRES_CONFIG, 'SLAVE'
    ):
        result['master'] = create_async_engine(
            config.POSTGRES_CONFIG.MASTER.URI, pool_recycle=3600
        )
        result['slave'] = create_async_engine(
            config.POSTGRES_CONFIG.SLAVE.URI, pool_recycle=3600
        )

    return result


engines = create_engines()


class ReadWriteRoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kw):
        if 'single_node' in engines:
            return engines['single_node'].sync_engine
        elif (
            self._flushing
            or self.in_transaction()
            or isinstance(clause, (Update, Insert, Delete))
        ):
            return engines['master'].sync_engine
        else:
            return engines['slave'].sync_engine


_async_session = async_sessionmaker(
    autocommit=False,
    autoflush=True,
    expire_on_commit=False,
    class_=AsyncSession,
    sync_session_class=ReadWriteRoutingSession,
)


async def init_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session() as session:
        yield session
