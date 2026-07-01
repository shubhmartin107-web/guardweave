from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import shlex
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from guardweave.sandbox.resource_limit import ResourceLimits

logger = logging.getLogger("guardweave.sandbox")


@dataclass
class SandboxResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    resource_violation: bool = False
    violation_reason: str = ""


class SandboxExecutor:
    def __init__(
        self,
        defaults: ResourceLimits | None = None,
        work_dir: str | Path | None = None,
    ):
        self._defaults = defaults or ResourceLimits()
        self._work_dir = Path(work_dir or tempfile.mkdtemp(prefix="guardweave_sandbox_"))

    async def execute(
        self,
        command: str | list[str],
        limits: ResourceLimits | None = None,
        env: dict[str, str] | None = None,
        cwd: str | Path | None = None,
    ) -> SandboxResult:
        limits = limits or self._defaults
        cwd = Path(cwd or self._work_dir)
        cwd.mkdir(parents=True, exist_ok=True)

        cmd_parts = shlex.split(command) if isinstance(command, str) else list(command)

        violation = self._check_command_violations(cmd_parts, limits)
        if violation:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=violation,
                duration_seconds=0.0,
                resource_violation=True,
                violation_reason=violation,
            )

        clean_env = self._build_env(env, limits)
        start_time = time.monotonic()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=clean_env,
                cwd=str(cwd),
                preexec_fn=self._make_preexec_fn(limits) if os.name != "nt" else None,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=limits.max_cpu_time_seconds
                )
                timed_out = False
            except TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    process.kill()
                stdout_bytes, stderr_bytes = await process.communicate()
                timed_out = True

            duration = time.monotonic() - start_time

            return SandboxResult(
                success=process.returncode == 0,
                exit_code=process.returncode if process.returncode is not None else -1,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
                duration_seconds=duration,
                timed_out=timed_out,
            )

        except FileNotFoundError:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command not found: {cmd_parts[0]}",
                duration_seconds=0.0,
                resource_violation=False,
                violation_reason=f"Command not found: {cmd_parts[0]}",
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_seconds=0.0,
            )

    def _check_command_violations(
        self, cmd_parts: list[str], limits: ResourceLimits
    ) -> str | None:
        if not cmd_parts:
            return "Empty command"

        base = Path(cmd_parts[0]).name.lower()

        for blocked in limits.blocked_commands:
            if base == blocked.lower() or base.endswith(f"/{blocked}"):
                return f"Command '{cmd_parts[0]}' is blocked by policy"

        if not limits.network_access:
            network_tools = {"curl", "wget", "nc", "ncat", "telnet", "ssh", "scp", "sftp"}
            if base in network_tools:
                return f"Network access is disabled. Command '{base}' blocked"

        if not limits.write_access:
            write_flags = {">", ">>", "dd", "mkfs", "touch"}
            for part in cmd_parts:
                if part in write_flags:
                    return f"Write access is disabled. Flag '{part}' blocked"

        return None

    def _build_env(
        self, env: dict[str, str] | None, limits: ResourceLimits
    ) -> dict[str, str]:
        clean_env: dict[str, str] = {}
        for key in limits.env_whitelist:
            if key in os.environ:
                clean_env[key] = os.environ[key]
        if env:
            for key, value in env.items():
                if key in limits.env_whitelist:
                    clean_env[key] = value
        return clean_env

    @staticmethod
    def _make_preexec_fn(limits: ResourceLimits) -> Callable[[], None]:
        def preexec():
            try:
                import resource

                if limits.max_cpu_time_seconds > 0:
                    resource.setrlimit(
                        resource.RLIMIT_CPU,
                        (limits.max_cpu_time_seconds, limits.max_cpu_time_seconds + 5),
                    )
                if limits.max_memory_mb > 0:
                    resource.setrlimit(
                        resource.RLIMIT_AS,
                        (limits.max_memory_mb * 1024 * 1024, limits.max_memory_mb * 1024 * 1024),
                    )
                if limits.max_processes > 0:
                    resource.setrlimit(
                        resource.RLIMIT_NPROC,
                        (limits.max_processes, limits.max_processes),
                    )
                if limits.max_disk_mb > 0:
                    resource.setrlimit(
                        resource.RLIMIT_FSIZE,
                        (limits.max_disk_mb * 1024 * 1024, limits.max_disk_mb * 1024 * 1024),
                    )
            except (OSError, ImportError):
                pass

        return preexec

    async def close(self) -> None:
        pass
