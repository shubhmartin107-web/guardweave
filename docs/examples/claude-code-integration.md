# Integrating GuardWeave with Claude Code

Claude Code is a powerful agentic coding tool that can execute commands, read/write files, and interact with the system. GuardWeave provides a safety layer that can intercept these actions and apply policy-based controls.

## How It Works

1. Claude Code is configured to call a pre-action hook script before executing each action
2. The hook sends the proposed action to GuardWeave for evaluation
3. GuardWeave checks the action against configured policies
4. If allowed, the action proceeds; if denied, Claude Code is blocked; if needs approval, the action is queued

## Setup

### 1. Install GuardWeave

```bash
pip install guardweave
```

### 2. Initialize and Apply a Policy

```bash
guardweave init
guardweave policy apply policies/strict.yaml
```

### 3. Configure Claude Code Hook

Add this to your Claude Code configuration (`.claude/settings.json` or environment variables):

```json
{
  "hooks": {
    "pre_action": "python3 /path/to/guardweave/examples/claude_code_hook.py --check"
  }
}
```

### 4. Run Claude Code

Claude Code will now check every action against GuardWeave policies before executing.

## Integration Script

The `examples/claude_code_hook.py` script maps Claude Code's tool names to GuardWeave capabilities:

| Claude Code Tool | GuardWeave Capability |
|-----------------|----------------------|
| Read | `file:read` |
| Write | `file:write` |
| Edit | `file:write` |
| Bash | `shell` |
| Glob | `file:read` |
| Grep | `file:read` |
| WebFetch | `network:http` |
| WebSearch | `network:http` |
| Task | `agent:spawn` |

## Example Scenarios

### Blocked: Dangerous shell command
```
$ claude "delete the temp directory"
Checking: Bash(rm -rf /tmp/data)
  -> BLOCKED: Action 'Bash' denied by policy. Reason: Shell execution requires human approval
```

### Allowed: Read operation
```
$ claude "read the config file"
Checking: Read(/etc/config.yaml)
  -> ALLOWED: Read operations are generally low risk
```

## Best Practices

1. **Start with the default policy** and refine based on your needs
2. **Use `ask` for risky operations** rather than blanket `deny`
3. **Check the audit log** regularly to see what Claude Code attempted
4. **Use the dashboard** to review and approve pending actions
