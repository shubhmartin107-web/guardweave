from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from guardweave.core.models import Policy
from guardweave.engine.policy_parser import load_policy_from_file

logger = logging.getLogger("guardweave.engine.loader")

PolicyChangeCallback = Callable[[Policy], None]


class PolicyDirectoryWatcher:
    def __init__(self, directory: str | Path):
        self._directory = Path(directory)
        self._loaded_policies: dict[str, Policy] = {}
        self._file_hashes: dict[str, str] = {}
        self._callbacks: list[PolicyChangeCallback] = []

    def on_change(self, callback: PolicyChangeCallback) -> None:
        self._callbacks.append(callback)

    def load_all(self) -> list[Policy]:
        self._directory.mkdir(parents=True, exist_ok=True)
        policies: list[Policy] = []

        for yaml_file in sorted(self._directory.glob("*.yaml")):
            try:
                policy = self._incremental_load(yaml_file)
                if policy:
                    policies.append(policy)
            except Exception as e:
                logger.warning("Failed to load policy %s: %s", yaml_file, e)

        return policies

    def refresh(self) -> list[Policy]:
        changed: list[Policy] = []
        for yaml_file in sorted(self._directory.glob("*.yaml")):
            try:
                new_hash = self._hash_file(yaml_file)
                old_hash = self._file_hashes.get(str(yaml_file))

                if new_hash != old_hash or str(yaml_file) not in self._loaded_policies:
                    policy = self._incremental_load(yaml_file)
                    if policy:
                        changed.append(policy)
                        for cb in self._callbacks:
                            try:
                                cb(policy)
                            except Exception:
                                logger.exception("Policy change callback failed")
            except Exception as e:
                logger.warning("Error refreshing policy %s: %s", yaml_file, e)

        return changed

    def _incremental_load(self, path: Path) -> Policy | None:
        policy = load_policy_from_file(path)
        policy_id = str(path)
        self._loaded_policies[policy_id] = policy
        self._file_hashes[policy_id] = self._hash_file(path)
        logger.info("Loaded policy: %s (from %s)", policy.name, path)
        return policy

    @staticmethod
    def _hash_file(path: Path) -> str:
        import hashlib

        return hashlib.sha256(path.read_bytes()).hexdigest()
