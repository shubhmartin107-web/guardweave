from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from guardweave.persistence.base import Base
from guardweave.persistence.models import (  # noqa: F401 - registers models
    ApprovalRequestModel,
    AuditEntryModel,
    PolicyModel,
    RuleModel,
)

DEFAULT_DB_PATH = Path.home() / ".guardweave" / "guardweave.db"


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_db_path() -> Path:
    env_path = os.environ.get("GUARDWEAVE_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        db_path = get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite+aiosqlite:///{db_path}"
        _engine = create_async_engine(db_url, echo=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def close_db():
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
