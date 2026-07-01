from __future__ import annotations

import asyncio
import cmd
from datetime import UTC, datetime
from typing import Any

from rich.console import Console
from rich.table import Table

from guardweave.persistence.database import get_session_factory, init_db
from guardweave.persistence.repositories import get_pending_approvals, get_recent_audit_entries

console = Console()


class GuardWeaveShell(cmd.Cmd):
    intro = """
    ╔══════════════════════════════════════╗
    ║       GuardWeave Interactive Shell   ║
    ║  Type 'help' for commands            ║
    ║  Type 'exit' or Ctrl+D to quit       ║
    ╚══════════════════════════════════════╝
    """
    prompt = "gw> "

    def __init__(self) -> None:
        super().__init__()
        self._factory: Any = None

    def _ensure_init(self) -> None:
        if self._factory is None:
            asyncio.run(init_db())
            self._factory = get_session_factory()

    def do_pending(self, arg: str) -> None:
        """Show pending approvals"""
        self._ensure_init()

        async def _run() -> None:
            async with self._factory() as session:
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
            table.add_column("Age")

            for req in pending:
                age = ""
                if req.requested_at:
                    delta = datetime.now(UTC) - req.requested_at.replace(tzinfo=None)
                    minutes = int(delta.total_seconds() / 60)
                    age = f"{minutes}m ago" if minutes < 60 else f"{minutes // 60}h {minutes % 60}m ago"
                table.add_row(
                    req.id[:16],
                    req.agent_id[:12],
                    req.action[:20],
                    req.capability.value if hasattr(req.capability, "value") else str(req.capability),
                    f"{req.risk_score} ({req.risk_level.value})",
                    age,
                )
            console.print(table)

        asyncio.run(_run())

    def do_logs(self, arg: str) -> None:
        """Show recent audit logs"""
        self._ensure_init()

        async def _run() -> None:
            async with self._factory() as session:
                entries = await get_recent_audit_entries(session, limit=20)

            if not entries:
                console.print("[yellow]No audit entries found.[/yellow]")
                return

            table = Table(title=f"Recent Audit Logs ({len(entries)} entries)")
            table.add_column("Time", style="cyan")
            table.add_column("Agent")
            table.add_column("Action")
            table.add_column("Capability")
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
                    e.capability.value if hasattr(e.capability, "value") else str(e.capability),
                    f"[green]{e.decision.value}[/green]" if e.decision.value == "allow" else (
                        f"[red]{e.decision.value}[/red]" if e.decision.value == "deny" else f"[yellow]{e.decision.value}[/yellow]"
                    ),
                    f"{e.risk_score} ({e.risk_level.value})",
                )
            console.print(table)

        asyncio.run(_run())

    def do_watch(self, arg: str) -> None:
        """Watch mode: continuously display approvals and logs (Ctrl+C to stop)"""
        self._ensure_init()

        try:
            interval = int(arg) if arg else 3
        except ValueError:
            interval = 3

        async def _watch() -> None:
            while True:
                async with self._factory() as session:
                    pending = await get_pending_approvals(session)

                console.clear()
                if pending:
                    table = Table(title=f"Pending Approvals (refreshing every {interval}s)")
                    table.add_column("ID", style="cyan")
                    table.add_column("Agent")
                    table.add_column("Action")
                    table.add_column("Risk")
                    for req in pending:
                        table.add_row(
                            req.id[:16], req.agent_id[:12], req.action[:25],
                            f"{req.risk_score} ({req.risk_level.value})",
                        )
                    console.print(table)
                else:
                    console.print("[green]No pending approvals. Watching...[/green]")

                await asyncio.sleep(interval)

        try:
            asyncio.run(_watch())
        except KeyboardInterrupt:
            console.print("\n[yellow]Watch mode stopped.[/yellow]")

    def do_status(self, arg: str) -> None:
        """Show system status overview"""
        self._ensure_init()

        async def _run() -> None:
            async with self._factory() as session:
                pending = await get_pending_approvals(session)
                recent = await get_recent_audit_entries(session, limit=5)

            console.print("[bold]GuardWeave Status[/bold]")
            console.print(f"  Pending approvals: {len(pending)}")
            console.print(f"  Recent entries: {len(recent)}")
            for e in recent:
                ts = e.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                console.print(f"    {ts.strftime('%H:%M:%S')} | {e.agent_id[:10]} | {e.action[:20]} | {e.decision.value}")

        asyncio.run(_run())

    def do_exit(self, arg: str) -> bool:
        """Exit the interactive shell"""
        console.print("[yellow]Goodbye![/yellow]")
        return True

    def do_EOF(self, arg: str) -> bool:
        return self.do_exit(arg)

    def default(self, line: str) -> None:
        console.print(f"[red]Unknown command: {line}. Type 'help'.[/red]")
