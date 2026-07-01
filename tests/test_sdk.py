import os

import pytest

from guardweave.core.enums import Capability
from guardweave.core.exceptions import ActionDeniedError, ActionRequiresApprovalError
from guardweave.engine.policy_parser import load_policy_from_file
from guardweave.persistence.database import init_db
from guardweave.persistence.repositories import save_policy
from guardweave.sdk.guardweave import GuardWeave


@pytest.fixture(autouse=True)
async def setup_policy():
    db_path = os.environ.get("GUARDWEAVE_DB_PATH", "/tmp/guardweave_test.db")
    os.environ["GUARDWEAVE_DB_PATH"] = db_path
    await init_db()
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    async with factory() as session:
        try:
            policy = load_policy_from_file("policies/default.yaml")
            await save_policy(session, policy)
        except FileNotFoundError:
            pass


@pytest.mark.asyncio
async def test_sdk_allow(setup_policy):
    gw = GuardWeave(
        agent_id="test-sdk",
        trust_level="medium",
        environment="development",
    )
    await gw.initialize()
    result = await gw.check_action(
        action="read",
        capability=Capability.FILE_READ,
        target="/tmp/test.txt",
    )
    assert result.decision.value == "allow"


@pytest.mark.asyncio
async def test_sdk_deny(setup_policy):
    gw = GuardWeave(
        agent_id="test-sdk",
        trust_level="medium",
        environment="development",
    )
    await gw.initialize()
    with pytest.raises(ActionDeniedError):
        await gw.check_action(
            action="get_secret",
            capability=Capability.SECRETS_ACCESS,
            target="/etc/ssl/cert.pem",
        )


@pytest.mark.asyncio
async def test_sdk_ask_requires_approval(setup_policy):
    gw = GuardWeave(
        agent_id="test-sdk",
        trust_level="medium",
        environment="development",
    )
    await gw.initialize()
    with pytest.raises(ActionRequiresApprovalError):
        await gw.check_action(
            action="run_shell",
            capability=Capability.SHELL,
            target="/bin/bash",
        )


@pytest.mark.asyncio
async def test_sdk_log_action(setup_policy):
    gw = GuardWeave(
        agent_id="test-sdk",
        trust_level="medium",
        environment="development",
    )
    await gw.initialize()
    await gw.log_action(
        action="manual_log",
        capability=Capability.API_CALL,
        decision="allow",
        risk_score=5,
        reason="test log",
    )
