# GuardWeave Policy Language

Policies define the rules that govern agent behavior. They are written in YAML and consist of a header section and a list of rules.

## Policy Structure

```yaml
name: policy-name
version: "1.0"
description: "Description of this policy"
trust_level: medium       # sandbox | low | medium | high | critical
environment: development  # development | staging | production
default_decision: ask     # allow | deny | ask

rules:
  - id: unique_rule_id
    description: "Human-readable description"
    match:
      capabilities: ["file:read"]
      targets: ["/tmp/*"]
      agents: ["agent-1"]
      sessions: ["session-abc"]
      risk_score_min: 0
      risk_score_max: 100
    decision: allow       # allow | deny | ask
    risk_score_modifier: 0
    reason: "Why this rule exists"
```

## Fields

### Header Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique policy name |
| `version` | No | Semantic version (default: "1.0") |
| `description` | No | Human-readable description |
| `trust_level` | No | Agent trust level this policy applies to |
| `environment` | No | Target environment |
| `default_decision` | No | Fallback if no rule matches (default: "ask") |

### Rule Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique rule identifier within this policy |
| `description` | No | Human-readable description |
| `match` | Yes | Conditions for this rule to apply |
| `decision` | Yes | What to do: `allow`, `deny`, or `ask` |
| `risk_score_modifier` | No | Adjust risk score (±) |
| `reason` | No | Explanation logged with the decision |

### Match Conditions

| Field | Type | Description |
|-------|------|-------------|
| `capabilities` | list | Capability names to match |
| `targets` | list | Glob patterns for action targets |
| `agents` | list | Specific agent IDs |
| `sessions` | list | Specific session IDs |
| `risk_score_min` | int | Minimum risk score |
| `risk_score_max` | int | Maximum risk score |

## Capabilities Reference

| Capability | Risk Score | Description |
|-----------|-----------|-------------|
| `file:read` | 10 | Read files from disk |
| `file:write` | 25 | Write files to disk |
| `file:delete` | 50 | Delete files |
| `file:execute` | 60 | Execute binary files |
| `network:http` | 15 | Make HTTP(S) requests |
| `network:raw` | 45 | Raw network access |
| `code:exec` | 70 | Execute code |
| `code:eval` | 65 | Evaluate code expressions |
| `shell` | 80 | Shell command execution |
| `api:call` | 20 | Call external APIs |
| `db:read` | 15 | Read from databases |
| `db:write` | 35 | Write to databases |
| `db:execute` | 55 | Execute database commands |
| `secrets:access` | 75 | Access secrets/credentials |
| `identity:impersonate` | 90 | Impersonate identities |
| `data:exfiltrate-sensitive` | 85 | Exfiltrate sensitive data |
| `agent:spawn` | 60 | Spawn sub-agents |
| `agent:terminate` | 70 | Terminate agents |
| `policy:modify` | 85 | Modify policies |
| `audit:modify` | 90 | Modify audit logs |

## Target Pattern Matching

Targets support Unix-style glob patterns:

- `*` matches any sequence of characters
- `?` matches any single character
- `[abc]` matches any character in the brackets
- `/etc/*` matches everything under `/etc/`
- `*/config.*` matches any file named `config.*` in any directory
- `https://api.example.com/*` matches any path under that domain

## Example Policies

### Development Policy (Balanced)
```yaml
name: development
trust_level: medium
environment: development
default_decision: ask
rules:
  - match: {capabilities: ["file:read", "db:read"]}
    decision: allow
  - match: {capabilities: ["secrets:access", "data:exfiltrate-sensitive"]}
    decision: deny
  - match: {capabilities: ["code:exec", "shell"]}
    decision: ask
```

### Production Policy (Strict)
```yaml
name: production-strict
trust_level: sandbox
environment: production
default_decision: deny
rules:
  - match: {capabilities: ["file:read"]}
    decision: allow
  - match: {capabilities: ["file:write", "file:delete"]}
    decision: ask
  - match: {capabilities: ["code:exec", "shell", "network:raw",
                           "secrets:access", "data:exfiltrate-sensitive"]}
    decision: deny
```

## Policy Evaluation Order

1. Find active policies matching the agent's environment and trust level
2. For each rule in the policy, check if the action matches all conditions
3. Return the decision from the **first matching rule**
4. If no rule matches, return the policy's `default_decision`

Rules should be ordered from most specific to least specific for clarity.
