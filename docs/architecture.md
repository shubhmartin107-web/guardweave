# GuardWeave Architecture

## Overview

GuardWeave is a modular, layered governance system for AI agents. It intercepts agent actions, evaluates them against configurable policies, scores their risk, and either allows, denies, or flags them for human approval — all while maintaining a tamper-evident audit trail.

## Layered Architecture

### Layer 1: SDK / Integration Layer
- **GuardWeave client** (`sdk/guardweave.py`): Main integration point for agents
- **Decorators** (`sdk/decorators.py`): `@guardweave()` for function-level protection
- **Middleware** (`sdk/middleware.py`): ASGI middleware for API endpoints
- **CLI** (`cli/`): Command-line tools for policy management, log inspection, and approvals

### Layer 2: Policy Engine
- **Policy Parser** (`engine/policy_parser.py`): Loads and validates YAML/JSON policies
- **Policy Evaluator** (`engine/evaluator.py`): Matches actions against policy rules
- **Risk Scorer** (`engine/risk_scorer.py`): Computes risk scores based on capability, trust level, and target

### Layer 3: Decision & Workflow
- **Decision Evaluator**: Returns allow/deny/ask for each action
- **HITL Workflow** (`hitl/workflow.py`): Manages approval request lifecycle
- **Escalation Handler** (`hitl/escalation.py`): Timeout-based escalation rules
- **Notification Hooks** (`hitl/notifications.py`): Pluggable notification system

### Layer 4: Audit & Observability
- **Audit Logger** (`audit/logger.py`): Structured logging of all decisions
- **Hash Chain** (`audit/hashing.py`): Merkle-chain for tamper-evident logs
- **Audit Exporter** (`audit/exporter.py`): JSON/CSV export

### Layer 5: Persistence
- **SQLite Database** via SQLAlchemy async
- **Repositories** for policies, audit entries, and approval requests
- All data is local and portable

### Layer 6: Interfaces
- **Gradio Dashboard**: 5-tab management interface
- **FastAPI**: REST API for programmatic access

## Data Flow

```
Agent Action
    │
    ▼
┌─────────────────────┐
│ SDK.check_action()  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Policy Evaluator    │
│ - Find matching     │
│   policy            │
│ - Match rules       │
│ - Score risk        │
└─────────┬───────────┘
          │
          ▼
    ┌─────┴─────┐
    │  Decision  │
    ├────┬────┬──┤
    │    │    │  │
    ▼    ▼   ▼   │
  Allow Deny Ask │
    │    │    │  │
    │    │    ▼  │
    │    │ ┌────┐│
    │    │ │HITL││
    │    │ │Work││
    │    │ │flow││
    │    │ └──┬─┘│
    │    │    │  │
    ▼    ▼    ▼  │
  ┌────────────────┐
  │ Audit Logger   │
  │ (hash chain)   │
  └───────┬────────┘
          │
          ▼
    ┌──────────┐
    │ SQLite   │
    │ Storage  │
    └──────────┘
```

## Key Design Decisions

### 1. SQLite for Portability
SQLite was chosen as the storage backend for zero-configuration setup, portability, and embedded deployment. For larger deployments, the repository pattern allows swapping in PostgreSQL or other backends.

### 2. Hash Chain for Audit Integrity
Each audit entry contains the hash of the previous entry, creating a cryptographic chain. Any retroactive modification breaks the chain and is immediately detectable via `AuditLogger.verify_integrity()`.

### 3. Policy Hot-Reload
Policies are cached in memory by the evaluator but can be refreshed by re-applying. The dashboard can trigger policy reloads.

### 4. Async-First Design
All I/O operations (database, audit logging, approval workflows) are async, making GuardWeave suitable for high-throughput agent systems.

### 5. Inference-Agnostic
The policy engine is purely rule-based and does not require any LLM inference for core evaluation. Plugable inference providers are supported for risk enrichment but are optional.
