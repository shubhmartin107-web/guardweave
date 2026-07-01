from __future__ import annotations

import asyncio
from datetime import UTC
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from guardweave.persistence.database import init_db
from guardweave.persistence.repositories import query_audit_logs

log_app = typer.Typer(help="Inspect GuardWeave audit logs")
console = Console()


@log_app.command("search")
def log_search(
    agent_id: str = typer.Option(None, "--agent", "-a", help="Filter by agent ID"),
    capability: str = typer.Option(None, "--capability", "-c", help="Filter by capability"),
    decision: str = typer.Option(None, "--decision", "-d", help="Filter by decision (allow/deny/ask)"),
    action: str = typer.Option(None, "--action", "-m", help="Filter by action name"),
    limit: int = typer.Option(50, "--limit", "-l", help="Number of entries to show"),
) -> None:
    """Search audit logs."""
    async def _run() -> None:
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            entries = await query_audit_logs(
                session,
                agent_id=agent_id,
                capability=capability,
                decision=decision,
                action=action,
                limit=limit,
            )

        if not entries:
            console.print("[yellow]No audit entries found.[/yellow]")
            return

        table = Table(title=f"Audit Logs ({len(entries)} entries)")
        table.add_column("Time", style="cyan")
        table.add_column("Agent")
        table.add_column("Action")
        table.add_column("Capability")
        table.add_column("Decision")
        table.add_column("Risk")
        table.add_column("Policy")

        for e in entries:
            ts = e.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            table.add_row(
                ts.strftime("%H:%M:%S"),
                e.agent_id[:10],
                e.action[:20],
                e.capability.value if hasattr(e.capability, 'value') else str(e.capability),
                f"[green]{e.decision.value}[/green]" if e.decision.value == "allow" else (
                    f"[red]{e.decision.value}[/red]" if e.decision.value == "deny" else f"[yellow]{e.decision.value}[/yellow]"
                ),
                f"{e.risk_score} ({e.risk_level.value})",
                e.policy_id[:10],
            )
        console.print(table)

    asyncio.run(_run())


@log_app.command("export")
def log_export(
    output: str = typer.Argument("audit_log.json", help="Output file path"),
    fmt: str = typer.Option("json", "--format", "-f", help="Export format (json/csv)"),
    limit: int = typer.Option(1000, "--limit", "-l", help="Number of entries to export"),
) -> None:
    """Export audit logs to a file."""
    async def _run() -> None:
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            entries = await query_audit_logs(session, limit=limit)

        from guardweave.audit.exporter import AuditExporter
        data = AuditExporter.to_csv(entries) if fmt == "csv" else AuditExporter.to_json(entries)

        Path(output).write_text(data)
        console.print(f"[green]Exported {len(entries)} entries to {output}[/green]")

    asyncio.run(_run())


@log_app.command("tail")
def log_tail(
    lines: int = typer.Option(20, "--lines", "-n", help="Number of recent entries"),
) -> None:
    """Show recent audit log entries (like tail -f)."""
    async def _run() -> None:
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            entries = await query_audit_logs(session, limit=lines)
        if not entries:
            console.print("[yellow]No audit entries found.[/yellow]")
            return
        table = Table(title=f"Recent Audit Logs ({len(entries)} entries)")
        table.add_column("Time", style="cyan")
        table.add_column("Agent")
        table.add_column("Action")
        table.add_column("Decision")
        table.add_column("Risk")
        for e in entries:
            ts = e.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            table.add_row(
                ts.strftime("%H:%M:%S"),
                e.agent_id[:10],
                e.action[:20],
                f"[green]{e.decision.value}[/green]" if e.decision.value == "allow" else (
                    f"[red]{e.decision.value}[/red]" if e.decision.value == "deny" else f"[yellow]{e.decision.value}[/yellow]"
                ),
                f"{e.risk_score} ({e.risk_level.value})",
            )
        console.print(table)
    asyncio.run(_run())
