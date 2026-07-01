from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from guardweave.engine.policy_parser import load_policy_from_file
from guardweave.persistence.database import init_db
from guardweave.persistence.repositories import (
    delete_policy,
    list_policies,
    load_policy_by_id,
    load_policy_by_name,
    save_policy,
)

policy_app = typer.Typer(help="Manage GuardWeave policies")
console = Console()


@policy_app.command("list")
def policy_list() -> None:
    """List all active policies."""
    async def _run() -> None:
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            policies = await list_policies(session)

        if not policies:
            console.print("[yellow]No policies found.[/yellow]")
            return

        table = Table(title="GuardWeave Policies")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Version")
        table.add_column("Trust Level")
        table.add_column("Environment")
        table.add_column("Rules")
        table.add_column("Active")

        for p in policies:
            table.add_row(
                p.id[:16],
                p.name,
                p.version,
                p.trust_level.value if hasattr(p.trust_level, 'value') else str(p.trust_level),
                p.environment,
                str(len(p.rules)),
                "Yes" if p.active else "No",
            )
        console.print(table)

    asyncio.run(_run())


@policy_app.command("view")
def policy_view(policy_id: str = typer.Argument(None, help="Policy ID or name")) -> None:
    """View a policy by ID or name."""
    async def _run() -> None:
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            policy = await load_policy_by_id(session, policy_id)
            if not policy:
                policy = await load_policy_by_name(session, policy_id)

        if not policy:
            console.print(f"[red]Policy not found: {policy_id}[/red]")
            raise typer.Exit(1)

        console.print(f"[bold]Policy:[/bold] {policy.name} (v{policy.version})")
        console.print(f"[bold]ID:[/bold] {policy.id}")
        console.print(f"[bold]Description:[/bold] {policy.description}")
        console.print(f"[bold]Trust Level:[/bold] {policy.trust_level}")
        console.print(f"[bold]Environment:[/bold] {policy.environment}")
        console.print(f"[bold]Default Decision:[/bold] {policy.default_decision}")
        console.print(f"[bold]Active:[/bold] {policy.active}")
        console.print(f"[bold]Rules:[/bold] {len(policy.rules)}")

        for i, rule in enumerate(policy.rules):
            console.print(f"\n  [cyan]Rule {i+1}:[/cyan] {rule.id}")
            console.print(f"    Description: {rule.description}")
            console.print(f"    Match: {rule.match.model_dump()}")
            console.print(f"    Decision: {rule.decision.value}")
            console.print(f"    Risk Modifier: {rule.risk_score_modifier}")

    asyncio.run(_run())


@policy_app.command("apply")
def policy_apply(
    file: str = typer.Argument(..., help="Path to YAML policy file"),
    name: str = typer.Option(None, help="Override policy name"),
) -> None:
    """Apply a policy from a YAML file."""
    async def _run() -> None:
        await init_db()
        path = Path(file)
        if not path.exists():
            console.print(f"[red]File not found: {path}[/red]")
            raise typer.Exit(1)

        try:
            policy = load_policy_from_file(path)
            if name:
                policy.name = name

            from guardweave.persistence.database import get_session_factory
            factory = get_session_factory()
            async with factory() as session:
                await save_policy(session, policy)

            console.print(f"[green]Policy applied:[/green] {policy.name} (id: {policy.id})")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    asyncio.run(_run())


@policy_app.command("delete")
def policy_delete(policy_id: str = typer.Argument(..., help="Policy ID to delete")) -> None:
    """Delete a policy by ID."""
    async def _run() -> None:
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            ok = await delete_policy(session, policy_id)

        if ok:
            console.print(f"[green]Deleted policy: {policy_id}[/green]")
        else:
            console.print(f"[red]Policy not found: {policy_id}[/red]")
            raise typer.Exit(1)

    asyncio.run(_run())


@policy_app.command("validate")
def policy_validate(file: str = typer.Argument(..., help="Path to YAML policy file")) -> None:
    """Validate a policy YAML file without applying it."""
    try:
        path = Path(file)
        policy = load_policy_from_file(path)
        console.print(f"[green]Valid policy:[/green] {policy.name} v{policy.version}")
        console.print(f"  Rules: {len(policy.rules)}")
        console.print(f"  Default decision: {policy.default_decision.value}")
        for i, rule in enumerate(policy.rules):
            console.print(f"  Rule {i+1}: {rule.id} -> {rule.decision.value}")
    except Exception as e:
        console.print(f"[red]Invalid policy:[/red] {e}")
        raise typer.Exit(1)
