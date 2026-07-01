"""Basic example of using GuardWeave SDK to protect an agent."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardweave import AsyncGuardWeave
from guardweave.core.enums import Capability, Decision
from guardweave.core.exceptions import ActionDeniedError, ActionRequiresApprovalError
from guardweave.engine.policy_parser import load_policy_from_file
from guardweave.persistence.database import get_session_factory, init_db
from guardweave.persistence.repositories import save_policy


async def main():
    # Initialize database and load a default policy
    await init_db()
    factory = get_session_factory()

    # Load and save the default policy
    try:
        policy = load_policy_from_file("policies/default.yaml")
        async with factory() as session:
            await save_policy(session, policy)
        print(f"Loaded policy: {policy.name}")
    except FileNotFoundError:
        print("No policies directory found; using SDK defaults")

    # Create a GuardWeave instance for our agent
    gw = AsyncGuardWeave(
        agent_id="demo-agent-1",
        trust_level="medium",
        environment="development",
    )

    await gw.initialize()

    # Scenario 1: Safe action (should be allowed)
    print("\n--- Scenario 1: Reading a file ---")
    try:
        result = await gw.check_action(
            action="read_config",
            capability=Capability.FILE_READ,
            target="/tmp/config.txt",
        )
        print(f"ALLOWED: risk={result.risk_score} ({result.risk_level.value})")
    except ActionDeniedError as e:
        print(f"DENIED: {e}")
    except ActionRequiresApprovalError as e:
        print(f"NEEDS APPROVAL: {e}")

    # Scenario 2: Dangerous action (should be denied)
    print("\n--- Scenario 2: Accessing secrets ---")
    try:
        result = await gw.check_action(
            action="get_secret",
            capability=Capability.SECRETS_ACCESS,
            target="/etc/ssl/cert.pem",
        )
        print(f"ALLOWED: risk={result.risk_score}")
    except ActionDeniedError as e:
        print(f"DENIED: {e}")
    except ActionRequiresApprovalError as e:
        print(f"NEEDS APPROVAL: {e}")

    # Scenario 3: Risky action requiring approval
    print("\n--- Scenario 3: Shell execution ---")
    try:
        result = await gw.check_action(
            action="run_command",
            capability=Capability.SHELL,
            target="/bin/bash",
        )
        print(f"ALLOWED: risk={result.risk_score}")
    except ActionDeniedError as e:
        print(f"DENIED: {e}")
    except ActionRequiresApprovalError as e:
        print(f"NEEDS APPROVAL: {e}")

    # Scenario 4: Manual audit logging
    print("\n--- Scenario 4: Manual log entry ---")
    await gw.log_action(
        action="user_login",
        capability=Capability.API_CALL,
        decision=Decision.ALLOW,
        risk_score=5,
        reason="User authentication",
    )
    print("Logged manual entry")

    print("\n=== Demo complete ===")


if __name__ == "__main__":
    asyncio.run(main())
