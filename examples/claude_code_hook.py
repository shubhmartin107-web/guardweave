"""Example of integrating GuardWeave with Claude Code as a pre-action hook.

Claude Code can be configured to call a hook script before each action.
This script checks the proposed action against GuardWeave policies.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardweave import AsyncGuardWeave
from guardweave.core.enums import Capability


def parse_claude_action(action_json: str) -> dict[str, Any]:
    """Parse a Claude Code action from its JSON format."""
    try:
        return json.loads(action_json)
    except json.JSONDecodeError:
        return {"action": action_json, "tool": "unknown"}


def map_to_capability(tool_name: str) -> Capability:
    """Map Claude Code tool names to GuardWeave capabilities."""
    tool_map = {
        "Read": Capability.FILE_READ,
        "Write": Capability.FILE_WRITE,
        "Edit": Capability.FILE_WRITE,
        "Bash": Capability.SHELL,
        "Tool": Capability.API_CALL,
        "Glob": Capability.FILE_READ,
        "Grep": Capability.FILE_READ,
        "WebFetch": Capability.NETWORK_HTTP,
        "WebSearch": Capability.NETWORK_HTTP,
        "Task": Capability.AGENT_SPAWN,
        "AskUser": Capability.API_CALL,
    }
    return tool_map.get(tool_name, Capability.API_CALL)


async def check_action(action_data: dict[str, Any]) -> dict[str, Any]:
    """Check a Claude Code action against GuardWeave policies.

    This function is intended to be called as a pre-action hook
    from Claude Code's configuration.

    Args:
        action_data: Dict with tool name, parameters, etc.

    Returns:
        Dict with 'allowed' (bool), 'reason' (str), and 'risk_score' (int).
    """
    tool_name = action_data.get("tool", "unknown")
    tool_input = action_data.get("input", action_data.get("command", ""))

    gw = AsyncGuardWeave(
        agent_id=os.environ.get("CLAUDE_CODE_AGENT_ID", "claude-code-agent"),
        environment=os.environ.get("GUARDWEAVE_ENV", "development"),
    )
    await gw.initialize()

    capability = map_to_capability(tool_name)

    try:
        result = await gw.check_action(
            action=tool_name,
            capability=capability,
            target=str(tool_input)[:200],
            parameters={"tool": tool_name, "input": str(tool_input)[:1000]},
        )
        return {
            "allowed": True,
            "reason": result.reason,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level.value,
        }
    except Exception as e:
        return {
            "allowed": False,
            "reason": str(e),
            "risk_score": 100,
            "risk_level": "high",
        }


async def main():
    # Simulate Claude Code actions
    test_actions = [
        {"tool": "Read", "input": "/tmp/test.py"},
        {"tool": "Bash", "input": "rm -rf /tmp/data"},
        {"tool": "Write", "input": "print('hello')", "path": "/etc/config.yaml"},
        {"tool": "WebSearch", "input": "latest AI papers"},
    ]

    for action in test_actions:
        print(f"\nChecking: {action['tool']}({action.get('input', '')[:50]})")
        result = await check_action(action)
        status = "ALLOWED" if result["allowed"] else "BLOCKED"
        print(f"  -> {status}: {result['reason'][:60]}")


if __name__ == "__main__":
    asyncio.run(main())
