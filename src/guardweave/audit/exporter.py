from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from guardweave.core.models import AuditEntry


class AuditExporter:
    @staticmethod
    def to_json(entries: list[AuditEntry], pretty: bool = True) -> str:
        data = [AuditExporter._entry_to_dict(e) for e in entries]
        indent = 2 if pretty else None
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)

    @staticmethod
    def to_csv(entries: list[AuditEntry]) -> str:
        output = io.StringIO()
        if not entries:
            return ""

        fieldnames = [
            "id", "timestamp", "agent_id", "session_id", "action",
            "capability", "target", "decision", "risk_score", "risk_level",
            "policy_id", "rule_id", "reason", "chain_hash", "previous_hash",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for e in entries:
            row = AuditExporter._entry_to_dict(e)
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def to_json_lines(entries: list[AuditEntry]) -> str:
        lines: list[str] = []
        for e in entries:
            lines.append(json.dumps(AuditExporter._entry_to_dict(e), default=str))
        return "\n".join(lines)

    @staticmethod
    def to_markdown(entries: list[AuditEntry]) -> str:
        if not entries:
            return "*No audit entries.*\n"

        lines = [
            "| Time | Agent | Action | Capability | Decision | Risk | Policy |",
            "|------|-------|--------|------------|----------|------|--------|",
        ]
        for e in entries[:100]:
            ts = e.timestamp.isoformat() if isinstance(e.timestamp, datetime) else str(e.timestamp)
            cap = e.capability.value if hasattr(e.capability, "value") else str(e.capability)
            dec = e.decision.value if hasattr(e.decision, "value") else str(e.decision)
            rl = e.risk_level.value if hasattr(e.risk_level, "value") else str(e.risk_level)
            lines.append(
                f"| {ts[:19]} | {e.agent_id[:12]} | {e.action[:20]} | {cap} "
                f"| {dec} | {e.risk_score}/{rl} | {e.policy_id[:12]} |"
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def export_to_file(
        entries: list[AuditEntry],
        path: str | Path,
        fmt: str = "json",
    ) -> Path:
        path = Path(path)
        fmt = fmt.lower()

        if fmt == "json":
            content = AuditExporter.to_json(entries)
        elif fmt == "jsonl":
            content = AuditExporter.to_json_lines(entries)
        elif fmt == "csv":
            content = AuditExporter.to_csv(entries)
        elif fmt == "md":
            content = AuditExporter.to_markdown(entries)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        path.write_text(content)
        return path

    @staticmethod
    def rotate_logs(
        log_dir: str | Path,
        max_entries: int = 10000,
        archive_prefix: str = "audit",
    ) -> list[Path]:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        archived: list[Path] = []
        current = log_dir / f"{archive_prefix}_current.json"

        if current.exists():
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            archive_path = log_dir / f"{archive_prefix}_{timestamp}.json"
            current.rename(archive_path)
            archived.append(archive_path)

        existing = sorted(log_dir.glob(f"{archive_prefix}_*.json"))
        while len(existing) > max(max_entries - 1, 0):
            old = existing.pop(0)
            old.unlink(missing_ok=True)

        return archived

    @staticmethod
    def _entry_to_dict(e: AuditEntry) -> dict[str, Any]:
        return {
            "id": e.id,
            "timestamp": e.timestamp.isoformat() if isinstance(e.timestamp, datetime) else str(e.timestamp),
            "agent_id": e.agent_id,
            "session_id": e.session_id,
            "action": e.action,
            "capability": e.capability.value if hasattr(e.capability, "value") else str(e.capability),
            "target": e.target,
            "decision": e.decision.value if hasattr(e.decision, "value") else str(e.decision),
            "risk_score": e.risk_score,
            "risk_level": e.risk_level.value if hasattr(e.risk_level, "value") else str(e.risk_level),
            "policy_id": e.policy_id,
            "rule_id": e.rule_id,
            "reason": e.reason,
            "chain_hash": e.chain_hash,
            "previous_hash": e.previous_hash,
            "context": e.context,
            "metadata": e.metadata,
        }
