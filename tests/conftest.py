import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from guardweave.persistence.database import get_session_factory, init_db

_test_db_path = None


def get_test_db_path():
    global _test_db_path
    if _test_db_path is None:
        _test_db_path = str(Path(tempfile.mkdtemp()) / "guardweave_test.db")
    return _test_db_path


@pytest.fixture(autouse=True)
def set_test_db():
    db_path = get_test_db_path()
    os.environ["GUARDWEAVE_DB_PATH"] = db_path
    yield
    # Cleanup after each test
    import guardweave.persistence.database as dbmod
    dbmod._engine = None
    dbmod._session_factory = None


@pytest.fixture
async def db_session():
    await init_db()
    factory = get_session_factory()
    async with factory() as session:
        yield session


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
