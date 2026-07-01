from __future__ import annotations

import typer

app = typer.Typer(
    name="guardweave",
    help="GuardWeave — Safety, Guardrails & Governance for AI Agents",
    no_args_is_help=True,
)


@app.command()
def version():
    """Print version information."""
    from guardweave.__version__ import __version__
    typer.echo(f"GuardWeave v{__version__}")


@app.command()
def init():
    """Initialize GuardWeave in the current directory."""
    from pathlib import Path

    cwd = Path.cwd()
    guardweave_dir = cwd / ".guardweave"
    guardweave_dir.mkdir(parents=True, exist_ok=True)

    policies_dir = guardweave_dir / "policies"
    policies_dir.mkdir(exist_ok=True)

    default_policy = policies_dir / "default.yaml"
    if not default_policy.exists():
        default_policy.write_text(
            """name: default
version: "1.0"
description: "Default GuardWeave policy"
trust_level: medium
environment: development
default_decision: ask
rules:
  - id: rule_allow_read
    description: "Allow read operations"
    match:
      capabilities: ["file:read", "db:read"]
    decision: allow
    reason: "Read operations are low risk"
  - id: rule_deny_dangerous
    description: "Block dangerous operations"
    match:
      capabilities: ["shell", "code:exec", "secrets:access"]
    decision: deny
    reason: "Dangerous operations blocked by default"
"""
        )

    typer.echo(f"Initialized GuardWeave in {cwd}")
    typer.echo(f"  Config dir: {guardweave_dir}")
    typer.echo(f"  Default policy: {default_policy}")


if __name__ == "__main__":
    app()

# Re-export subcommands from other modules
from guardweave.cli.agent_cmds import agent_app
from guardweave.cli.log_cmds import log_app
from guardweave.cli.policy_cmds import policy_app

app.add_typer(policy_app, name="policy", help="Manage policies")
app.add_typer(log_app, name="log", help="Inspect audit logs")
app.add_typer(agent_app, name="agent", help="Manage agents & approvals")
