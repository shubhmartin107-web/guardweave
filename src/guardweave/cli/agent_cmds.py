from __future__ import annotations

import asyncio
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from guardweave.persistence.database import init_db
from guardweave.persistence.repositories import get_pending_approvals

agent_app = typer.Typer(help="Manage agents and approvals")
console = Console()


@agent_app.command("list")
def agent_list() -> None:
    """List active agents from audit logs."""
    async def _run() -> None:
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            from guardweave.persistence.repositories import get_agent_count, query_audit_logs
            await get_agent_count(session)
            recent = await query_audit_logs(session, limit=100)

        agent_sessions: dict[tuple[str, str], dict[str, Any]] = {}
        for e in recent:
            key = (e.agent_id, e.session_id)
            if key not in agent_sessions:
                agent_sessions[key] = {
                    "agent_id": e.agent_id,
                    "session_id": e.session_id,
                    "last_action": e.action,
                    "last_seen": e.timestamp,
                    "actions": 0,
                }
            agent_sessions[key]["actions"] += 1

        if not agent_sessions:
            console.print("[yellow]No agents found.[/yellow]")
            return

        table = Table(title=f"Active Agents ({len(agent_sessions)} unique sessions)")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Session")
        table.add_column("Last Action")
        table.add_column("Last Seen")
        table.add_column("Actions")

        for _key, data in agent_sessions.items():
            table.add_row(
                data["agent_id"][:16],
                data["session_id"][:10],
                data["last_action"][:20],
                data["last_seen"].strftime("%H:%M:%S") if hasattr(data["last_seen"], "strftime") else str(data["last_seen"]),
                str(data["actions"]),
            )
        console.print(table)

    asyncio.run(_run())


@agent_app.command("approvals")
def agent_approvals() -> None:
    """List pending approval requests."""
    async def _run() -> None:
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            pending = await get_pending_approvals(session)

        if not pending:
            console.print("[green]No pending approvals.[/green]")
            return

        table = Table(title=f"Pending Approvals ({len(pending)})")
        table.add_column("ID", style="cyan")
        table.add_column("Agent")
        table.add_column("Action")
        table.add_column("Capability")
        table.add_column("Risk")
        table.add_column("Requested")

        for req in pending:
            table.add_row(
                req.id[:16],
                req.agent_id[:12],
                req.action[:20],
                req.capability.value if hasattr(req.capability, 'value') else str(req.capability),
                f"{req.risk_score} ({req.risk_level.value})",
                req.requested_at.strftime("%Y-%m-%d %H:%M") if req.requested_at else "",
            )
        console.print(table)

    asyncio.run(_run())


@agent_app.command("approve")
def agent_approve(
    approval_id: str = typer.Argument(..., help="Approval request ID"),
    feedback: str = typer.Option(None, "--feedback", "-f", help="Optional feedback"),
) -> None:
    """Approve a pending request."""
    async def _run() -> None:
        await init_db()
        from guardweave.hitl.workflow import ApprovalWorkflow
        from guardweave.persistence.database import get_session_factory

        factory = get_session_factory()
        workflow = ApprovalWorkflow()
        async with factory() as session:
            req = await workflow.approve(session, approval_id, decided_by="cli", feedback=feedback)

        if req:
            console.print(f"[green]Approved:[/green] {req.id}")
        else:
            console.print(f"[red]Approval request not found: {approval_id}[/red]")
            raise typer.Exit(1)

    asyncio.run(_run())


@agent_app.command("deny")
def agent_deny(
    approval_id: str = typer.Argument(..., help="Approval request ID"),
    feedback: str = typer.Option(None, "--feedback", "-f", help="Optional feedback"),
) -> None:
    """Deny a pending request."""
    async def _run() -> None:
        await init_db()
        from guardweave.hitl.workflow import ApprovalWorkflow
        from guardweave.persistence.database import get_session_factory

        factory = get_session_factory()
        workflow = ApprovalWorkflow()
        async with factory() as session:
            req = await workflow.deny(session, approval_id, decided_by="cli", feedback=feedback)

        if req:
            console.print(f"[red]Denied:[/red] {req.id}")
        else:
            console.print(f"[red]Approval request not found: {approval_id}[/red]")
            raise typer.Exit(1)

    asyncio.run(_run())


@agent_app.command("shell")
def agent_shell() -> None:
    """Launch interactive GuardWeave shell."""
    from guardweave.cli.shell import GuardWeaveShell
    GuardWeaveShell().cmdloop()


@agent_app.command("watch")
def agent_watch(
    interval: int = typer.Option(3, "--interval", "-i", help="Refresh interval in seconds"),
) -> None:
    """Watch mode: continuously display approvals (Ctrl+C to stop)."""
    from guardweave.cli.shell import GuardWeaveShell
    shell = GuardWeaveShell()
    shell.do_watch(str(interval))


@agent_app.command("dashboard")
def agent_dashboard(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(7860, "--port", "-p", help="Port to bind to"),
) -> None:
    """Launch the GuardWeave dashboard."""
    from guardweave.dashboard.app import CSS, create_dashboard
    from guardweave.dashboard.theme import create_theme
    dashboard = create_dashboard()
    theme = create_theme()
    dashboard.launch(server_name=host, server_port=port, theme=theme, css=CSS)
