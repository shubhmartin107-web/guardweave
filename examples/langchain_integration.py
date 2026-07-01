"""Example of integrating GuardWeave with LangChain via custom callback."""

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardweave import AsyncGuardWeave
from guardweave.core.enums import Capability
from guardweave.core.exceptions import ActionDeniedError


class GuardWeaveLangChainCallback:
    """A LangChain callback handler that checks every tool call against GuardWeave policies.

    Usage:
        from langchain.agents import AgentExecutor
        from langchain.agents import create_react_agent

        guard = GuardWeaveLangChainCallback(agent_id="my-agent")
        agent = AgentExecutor(
            agent=agent,
            tools=tools,
            callbacks=[guard],
            handle_parsing_errors=True,
        )
    """

    def __init__(
        self,
        agent_id: str = "langchain-agent",
        environment: str = "development",
    ):
        self._gw = AsyncGuardWeave(
            agent_id=agent_id,
            environment=environment,
        )
        self._initialized = False

    async def _ensure_init(self):
        if not self._initialized:
            await self._gw.initialize()
            self._initialized = True

    def _map_tool_to_capability(self, tool_name: str) -> Capability:
        tool_lower = tool_name.lower()
        mapping = {
            "python": Capability.CODE_EXEC,
            "python_repl": Capability.CODE_EXEC,
            "shell": Capability.SHELL,
            "bash": Capability.SHELL,
            "terminal": Capability.SHELL,
            "read_file": Capability.FILE_READ,
            "file_read": Capability.FILE_READ,
            "write_file": Capability.FILE_WRITE,
            "file_write": Capability.FILE_WRITE,
            "delete_file": Capability.FILE_DELETE,
            "search": Capability.NETWORK_HTTP,
            "web_search": Capability.NETWORK_HTTP,
            "requests_get": Capability.NETWORK_HTTP,
            "requests_post": Capability.API_CALL,
            "api": Capability.API_CALL,
            "database": Capability.DB_READ,
            "db_query": Capability.DB_READ,
            "db_write": Capability.DB_WRITE,
        }
        for key, cap in mapping.items():
            if key in tool_lower:
                return cap
        return Capability.API_CALL

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        await self._ensure_init()
        tool_name = serialized.get("name", "unknown")

        capability = self._map_tool_to_capability(tool_name)

        try:
            result = await self._gw.check_action(
                action=tool_name,
                capability=capability,
                target=input_str[:100],
                parameters={"input": input_str[:500]},
            )
            print(f"[GuardWeave] Tool '{tool_name}' -> {result.decision.value} (risk={result.risk_score})")
        except ActionDeniedError as e:
            print(f"[GuardWeave] BLOCKED: {e}")
            raise
        except Exception as e:
            if "requires approval" in str(e):
                print(f"[GuardWeave] PENDING APPROVAL: {e}")
            else:
                print(f"[GuardWeave] Error: {e}")


async def demo():
    """Demonstrate the GuardWeave-LangChain integration."""
    callback = GuardWeaveLangChainCallback(agent_id="demo-langchain-agent")
    await callback._ensure_init()

    test_cases = [
        ("read_file", "/tmp/data.txt"),
        ("bash", "rm -rf /"),
        ("web_search", "latest AI news"),
        ("write_file", "/etc/config.yaml"),
    ]

    for tool_name, tool_input in test_cases:
        print(f"\nTool: {tool_name}(input={tool_input!r})")
        try:
            await callback.on_tool_start(
                serialized={"name": tool_name},
                input_str=tool_input,
            )
            print("  -> Proceeding (allowed or would require approval)")
        except ActionDeniedError as e:
            print(f"  -> BLOCKED: {e}")
        except Exception as e:
            print(f"  -> {e}")


if __name__ == "__main__":
    asyncio.run(demo())
