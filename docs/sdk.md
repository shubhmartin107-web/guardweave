# GuardWeave SDK Guide

The GuardWeave SDK provides three ways to integrate safety controls into your AI agents.

## 1. Direct SDK Client

The `GuardWeave` class is the primary integration point.

### Basic Usage

```python
import asyncio
from guardweave import GuardWeave
from guardweave.core.enums import Capability
from guardweave.core.exceptions import ActionDeniedError, ActionRequiresApprovalError

async def main():
    gw = GuardWeave(
        agent_id="my-agent",
        trust_level="medium",
        environment="development",
    )
    await gw.initialize()

    try:
        result = await gw.check_action(
            action="read_file",
            capability=Capability.FILE_READ,
            target="/tmp/data.txt",
        )
        print(f"Allowed with risk score: {result.risk_score}")
        # >>> Proceed with the action
    except ActionDeniedError as e:
        print(f"Blocked: {e}")
    except ActionRequiresApprovalError as e:
        print(f"Pending approval: {e}")

asyncio.run(main())
```

### API Reference

#### `GuardWeave.__init__()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_id` | `str` | Auto-generated | Unique agent identifier |
| `session_id` | `str` | Auto-generated | Session identifier |
| `trust_level` | `TrustLevel` | `MEDIUM` | Agent trust level |
| `environment` | `str` | `"development"` | Runtime environment |

#### `GuardWeave.check_action()`

Check whether an action is allowed, denied, or requires approval.

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | `str` | Action name/description |
| `capability` | `Capability` | The capability required |
| `target` | `str` | Action target (file path, URL, etc.) |
| `parameters` | `dict` | Optional action parameters |
| `metadata` | `dict` | Additional metadata for audit |

**Returns:** `PolicyEvaluationResult` if allowed
**Raises:** `ActionDeniedError` or `ActionRequiresApprovalError`

#### `GuardWeave.log_action()`

Write a manual audit log entry.

#### `GuardWeave.request_approval()`

Manually create an approval request.

#### `GuardWeave.check_approval_status()`

Check the status of an approval request by ID.

## 2. Decorators

The `@guardweave()` decorator wraps agent functions with policy checks.

```python
from guardweave.sdk.decorators import guardweave
from guardweave.core.enums import Capability

class FileManager:
    @guardweave(capability=Capability.FILE_READ)
    async def read(self, path: str):
        with open(path) as f:
            return f.read()

    @guardweave(capability=Capability.FILE_WRITE)
    async def write(self, path: str, content: str):
        with open(path, "w") as f:
            f.write(content)
```

### Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `capability` | `Capability` | Required | Capability to check |
| `trust_level` | `TrustLevel` | `MEDIUM` | Agent trust level |
| `environment` | `str` | `None` | Runtime environment |
| `agent_id` | `str` | `None` | Agent identifier |
| `deny_message` | `str` | Default message | Message when action is denied |
| `raise_on_deny` | `bool` | `True` | Whether to raise on denial |

## 3. ASGI Middleware

For protecting API endpoints:

```python
from fastapi import FastAPI
from guardweave.sdk.middleware import GuardWeaveMiddleware

app = FastAPI()
app.add_middleware(
    GuardWeaveMiddleware,
    agent_id="api-gateway",
    trust_level="medium",
    environment="production",
    excluded_paths=["/health", "/docs", "/openapi.json"],
)
```

## 4. LangChain Integration

Use the callback handler for LangChain agents:

```python
from guardweave.examples.langchain_integration import GuardWeaveLangChainCallback

guard = GuardWeaveLangChainCallback(agent_id="my-agent")

# Pass as callback to LangChain agent
agent = AgentExecutor(
    agent=agent,
    tools=tools,
    callbacks=[guard],
)
```

## 5. Claude Code Integration

Use the pre-action hook for Claude Code:

```python
from guardweave.examples.claude_code_hook import check_action

# In Claude Code's config, call this before each action
result = await check_action({"tool": "Bash", "input": "rm -rf /"})
if not result["allowed"]:
    print(f"Blocked: {result['reason']}")
```

## Error Handling

```python
from guardweave.core.exceptions import (
    ActionDeniedError,       # Action was denied by policy
    ActionRequiresApprovalError,  # Action needs human approval
    PolicyNotFoundError,     # No matching policy found
    ApprovalTimeoutError,    # Approval request timed out
)
```
