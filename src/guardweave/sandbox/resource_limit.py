from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResourceLimits:
    max_cpu_time_seconds: int = 30
    max_memory_mb: int = 512
    max_disk_mb: int = 100
    max_processes: int = 10
    allowed_paths: list[str] = field(default_factory=lambda: [tempfile.gettempdir()])
    blocked_paths: list[str] = field(default_factory=lambda: ["/etc", "/home", "/root", "/var"])
    blocked_commands: list[str] = field(default_factory=lambda: [
        "sudo", "su", "chmod", "chown", "mount", "umount",
        "mkfs", "dd", "fdisk", "reboot", "shutdown", "init",
        "iptables", "ufw", "passwd", "useradd", "usermod",
    ])
    env_whitelist: list[str] = field(default_factory=lambda: [
        "PATH", "HOME", "USER", "LANG", "LC_ALL", "PYTHONPATH",
    ])
    network_access: bool = False
    write_access: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_cpu_time_seconds": self.max_cpu_time_seconds,
            "max_memory_mb": self.max_memory_mb,
            "max_disk_mb": self.max_disk_mb,
            "max_processes": self.max_processes,
            "network_access": self.network_access,
            "write_access": self.write_access,
        }
