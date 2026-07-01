# GuardWeave

**Safety, Guardrails & Governance Layer for AI Agents**

GuardWeave is an open-source infrastructure layer that provides structured safety controls, permission management, auditability, and human oversight for AI agent deployments. It addresses one of the biggest barriers to production agent adoption: the lack of robust safety, permissioning, oversight, and auditability.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![CI](https://github.com/shubhmartin107-web/guardweave/actions/workflows/ci.yml/badge.svg)](https://github.com/shubhmartin107-web/guardweave/actions/workflows/ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Tests: 32 passing](https://img.shields.io/badge/tests-32%20passing-brightgreen)](tests/)

---

## Why GuardWeave?

Most current agent systems operate with minimal or no safety controls. Agents can perform unintended or harmful actions, access sensitive resources, or run without proper oversight. As agents become more autonomous and long-running, the absence of structured guardrails, permission systems, and human oversight makes production deployment risky and often impractical.

**GuardWeave provides:**
- **Structured guardrails** that don't overly restrict agent capability
- **Fine-grained permissioning** — declare what each agent can do
- **Human-in-the-loop approvals** for high-risk actions
- **Tamper-evident audit trails** — know exactly what happened and why
- **Policy-driven governance** — YAML policies that are easy to write and audit

## Features

| Feature | Description |
|---------|-------------|
| **Capability & Permission System** | Declare agent capabilities (file access, web, code exec, API calls) with allow/deny/ask rules per trust level |
| **Policy Engine** | YAML/JSON-based policies with risk scoring, pre-execution checks, and custom rules |
| **Human-in-the-Loop** | Configurable approval gates, escalation rules, timeout handling, and feedback |
| **Audit Logging** | Tamper-evident Merkle-chain audit logs with full traceability and integrity verification |
| **Gradio Dashboard** | Monitor agents, manage policies, review approvals, and search audit logs |
| **Python SDK** | Decorator-based integration with async support |
| **CLI Tools** | Full command-line interface for policy management, log inspection, and approvals |
| **FastAPI Backend** | REST API for programmatic access to all features |
| **Pluggable Inference** | Works with any LLM provider (DeepSeek, Gemini, Groq, Ollama) — policy evaluation is inference-agnostic |

## Quick Start

### Installation

```bash
pip install guardweave
```

### Initialize

```bash
guardweave init
```

### Apply a Policy

```bash
guardweave policy apply policies/default.yaml
```

### Launch the Dashboard

```bash
guardweave agent dashboard
```

Open http://127.0.0.1:7860 in your browser.

### SDK Usage

```python
import asyncio
from guardweave import AsyncGuardWeave
from guardweave.core.enums import Capability
from guardweave.core.exceptions import ActionDeniedError

async def main():
    gw = AsyncGuardWeave(
        agent_id="my-agent",
        trust_level="medium",
        environment="development",
    )
    await gw.initialize()

    # Check an action before execution
    result = await gw.check_action(
        action="read_file",
        capability=Capability.FILE_READ,
        target="/tmp/data.txt",
    )
    print(f"Allowed: {result.decision.value} (risk: {result.risk_score})")

asyncio.run(main())
```

### Using the Decorator

```python
from guardweave.sdk.decorators import guardweave
from guardweave.core.enums import Capability

class MyAgent:
    @guardweave(capability=Capability.FILE_READ)
    async def read_file(self, path: str):
        # GuardWeave checks the action before this runs
        with open(path) as f:
            return f.read()
```

### CLI Commands

```
guardweave policy list          # List all policies
guardweave policy apply file.yaml   # Apply a policy
guardweave policy validate file.yaml # Validate a policy
guardweave log search            # Search audit logs
guardweave log export logs.json  # Export logs
guardweave agent list            # List active agents
guardweave agent approvals       # Show pending approvals
guardweave agent approve <id>    # Approve a request
guardweave agent deny <id>       # Deny a request
guardweave agent dashboard       # Launch the dashboard
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           AI Agent (your code)                       │
│  ┌──────────┐  ┌───────────┐  ┌─────────────────┐  │
│  │ SDK      │  │ Decorator │  │ Middleware       │  │
│  └────┬─────┘  └─────┬─────┘  └───────┬─────────┘  │
├───────┴──────────────┴─────────────────┴────────────┤
│              GuardWeave Core                         │
│  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │ Policy     │→ │ Risk       │→ │ Decision       │  │
│  │ Engine     │  │ Scorer     │  │ Evaluator      │  │
│  └─────┬──────┘  └────────────┘  └───────┬───────┘  │
│        │                                  │          │
│  ┌─────▼──────┐                  ┌───────▼───────┐  │
│  │ Policy     │                  │ HITL/Approval │  │
│  │ Storage    │                  │ Workflow      │  │
│  └────────────┘                  └───────┬───────┘  │
│  ┌──────────────────────────────────────┼─────────┐ │
│  │       Audit System (Hash Chain)      │         │ │
│  └──────────────────────────────────────┴─────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │              SQLite Storage                     │ │
│  │  [Policies] [Audit Logs] [Approval Requests]   │ │
│  └────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────┤
│  CLI         Gradio Dashboard      FastAPI          │
└────────────────────────────────────────────────────┘
```

## Policy Language

Policies are defined in YAML with a simple but expressive structure:

```yaml
name: my-policy
version: "1.0"
description: "Production policy for research agents"
trust_level: medium
environment: production
default_decision: ask

rules:
  - id: allow_web_search
    description: "Allow web search via HTTP"
    match:
      capabilities: ["network:http"]
      targets: ["https://api.duckduckgo.com/*"]
    decision: allow
    reason: "Web research is permitted"

  - id: deny_system_write
    description: "Block writes to system directories"
    match:
      capabilities: ["file:write"]
      targets: ["/etc/*", "/usr/*"]
    decision: deny
    reason: "System directory writes are prohibited"

  - id: ask_code_exec
    description: "Require approval for code execution"
    match:
      capabilities: ["code:exec", "shell"]
    decision: ask
    reason: "Code execution requires human oversight"
```

See [docs/policies.md](docs/policies.md) for the full reference.

## Risk Scoring

Each capability has a base risk score, modified by agent trust level and target:

| Capability | Base Risk | Example Modifiers |
|-----------|-----------|-------------------|
| `file:read` | 10 | +10 for system paths |
| `file:write` | 25 | +20 for sensitive paths |
| `shell` | 80 | +20 for sensitive targets |
| `secrets:access` | 75 | +20 for credential files |
| `code:exec` | 70 | -30% for HIGH trust agents |

## Human-in-the-Loop Workflow

1. Agent requests an action that matches an "ask" rule
2. GuardWeave creates a pending approval request with full context
3. Human reviews on the dashboard or via CLI
4. Human approves/denies with optional feedback
5. If no response within timeout: auto-escalate or auto-deny based on risk level
6. All decisions are logged to the tamper-evident audit chain

## Audit Integrity

GuardWeave uses a **Merkle hash chain** for audit logs. Each entry contains:

- `previous_hash`: The hash of the previous entry
- `chain_hash`: The SHA-256 hash of the current entry's data

This creates a cryptographic chain where tampering with any entry breaks the chain and is immediately detectable.

```bash
# Verify audit chain integrity
guardweave agent dashboard -> Settings -> "Verify Audit Chain"
```

## Integration Examples

- **Claude Code**: Use `examples/claude_code_hook.py` as a pre-action hook
- **LangChain**: Use `examples/langchain_integration.py` with the callback handler
- **Custom Agents**: Use the decorator-based SDK from `examples/basic_agent.py`
- **Custom Policies**: See `examples/custom_policy.py` for programmatic policy creation

## Comparison with Other Tools

| Feature | GuardWeave | DIY | Other Tools |
|---------|-----------|-----|-------------|
| Policy engine | ✅ YAML-based, rule matching | ❌ Must build from scratch | Limited |
| Human-in-the-loop | ✅ Escalation & timeouts | ❌ Requires custom infra | Limited |
| Audit chain | ✅ Tamper-evident hash chain | ❌ Basic logging | ❌ |
| Dashboard | ✅ Gradio, 5 tabs | ❌ | Basic |
| Open source | ✅ MIT | ✅ | ❌ Often proprietary |
| SDK/decorators | ✅ Python, async | ❌ | ❌ |

## Running with Docker

```bash
docker compose up
```

This starts the API server on port 8000 and the dashboard on port 7860.

## Development

```bash
# Clone and install
git clone https://github.com/shubhmartin107-web/guardweave.git
cd guardweave
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

## Vision

GuardWeave's long-term vision is to make safe, auditable, and governable agent systems accessible to everyone through open source. We believe that safety infrastructure should not be a barrier to entry, and that the ecosystem needs standardized, composable governance layers — just as web applications need authentication and authorization middleware.

**The goal:** Every AI agent, from personal assistants to production-grade autonomous systems, should benefit from structured guardrails, clear permission boundaries, and human oversight by default.

## License

MIT License. See [LICENSE](LICENSE) for details.
