# GuardWeave CLI Reference

## Global Commands

### `guardweave version`
Print version information.

### `guardweave init`
Initialize GuardWeave in the current directory. Creates a `.guardweave/` directory with a default policy.

## Policy Management

### `guardweave policy list`
List all active policies.

### `guardweave policy view <id>`
View policy details by ID or name.

### `guardweave policy apply <file>`
Apply a policy from a YAML file.

```bash
guardweave policy apply policies/my-policy.yaml
```

### `guardweave policy delete <id>`
Delete a policy by ID.

### `guardweave policy validate <file>`
Validate a policy YAML file without applying it.

```bash
guardweave policy validate policies/default.yaml
```

## Audit Logs

### `guardweave log search`
Search audit logs with optional filters.

```bash
guardweave log search --agent my-agent --capability file:read --decision deny --limit 20
```

Options:
- `--agent, -a`: Filter by agent ID
- `--capability, -c`: Filter by capability
- `--decision, -d`: Filter by decision (allow/deny/ask)
- `--limit, -l`: Number of entries (default: 50)

### `guardweave log export <output>`
Export audit logs to JSON or CSV.

```bash
guardweave log export logs.json
guardweave log export logs.csv --format csv
```

### `guardweave log tail`
Show recent audit log entries (default: 20).

## Agent & Approval Management

### `guardweave agent list`
List active agent sessions.

### `guardweave agent approvals`
Show pending approval requests.

### `guardweave agent approve <id>`
Approve a pending request.

```bash
guardweave agent approve apr_abc123 --feedback "Looks safe"
```

### `guardweave agent deny <id>`
Deny a pending request.

```bash
guardweave agent deny apr_abc123 --feedback "Not authorized"
```

### `guardweave agent dashboard`
Launch the Gradio dashboard.

```bash
guardweave agent dashboard --host 0.0.0.0 --port 7860
```
