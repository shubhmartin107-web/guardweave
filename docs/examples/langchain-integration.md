# Integrating GuardWeave with LangChain

LangChain is a popular framework for building agentic applications. GuardWeave integrates with LangChain through a callback handler that intercepts tool calls and checks them against policies.

## How It Works

1. The `GuardWeaveLangChainCallback` is passed as a callback to the LangChain agent
2. Before each tool call, the callback checks the action against GuardWeave policies
3. The agent is blocked from executing tools that are denied or require approval
4. All decisions are logged to the audit chain

## Setup

### 1. Install Dependencies

```bash
pip install guardweave langchain
```

### 2. Create the Callback

```python
from guardweave.examples.langchain_integration import GuardWeaveLangChainCallback

guard = GuardWeaveLangChainCallback(
    agent_id="my-langchain-agent",
    environment="development",
)
```

### 3. Attach to Agent

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool

@tool
def read_file(path: str) -> str:
    """Read a file from disk."""
    with open(path) as f:
        return f.read()

tools = [read_file]

agent = create_react_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    callbacks=[guard],
    handle_parsing_errors=True,
    verbose=True,
)
```

## Capability Mapping

The callback automatically maps tool names to GuardWeave capabilities:

| Tool Name Pattern | GuardWeave Capability |
|------------------|----------------------|
| `python`, `python_repl` | `code:exec` |
| `shell`, `bash`, `terminal` | `shell` |
| `read_file`, `file_read` | `file:read` |
| `write_file`, `file_write` | `file:write` |
| `delete_file` | `file:delete` |
| `search`, `web_search` | `network:http` |
| `requests_get` | `network:http` |
| `requests_post` | `api:call` |
| `database`, `db_query` | `db:read` |
| `db_write` | `db:write` |
| Default | `api:call` |

## Example

```python
from langchain.agents import tool

@tool
def write_config(path: str, content: str) -> str:
    """Write configuration to a file."""
    with open(path, "w") as f:
        f.write(content)
    return f"Written to {path}"

# This will be intercepted by GuardWeave:
result = agent_executor.invoke({"input": "write /etc/nginx.conf with proxy settings"})
# -> GuardWeave will check file:write capability against the policy
```
