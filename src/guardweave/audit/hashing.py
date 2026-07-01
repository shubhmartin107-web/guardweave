from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any


class HashChain:
    _secret: bytes

    def __init__(self, secret: str | None = None):
        if secret is None:
            secret = os.environ.get("GUARDWEAVE_CHAIN_SECRET", "guardweave-chain-secret-change-in-production")
        self._secret = secret.encode("utf-8")

    def compute_hash(self, data: dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def compute_hmac(self, data: dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hmac.new(self._secret, serialized, hashlib.sha256).hexdigest()

    def build_entry_data(
        self,
        entry_id: str,
        timestamp: datetime,
        agent_id: str,
        session_id: str,
        action: str,
        capability: str,
        target: str,
        decision: str,
        risk_score: int,
        risk_level: str,
        policy_id: str,
        rule_id: str | None,
        reason: str,
        context: dict[str, Any],
        previous_hash: str,
    ) -> dict[str, Any]:
        return {
            "id": entry_id,
            "timestamp": timestamp.isoformat(),
            "agent_id": agent_id,
            "session_id": session_id,
            "action": action,
            "capability": capability,
            "target": target,
            "decision": decision,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "policy_id": policy_id,
            "rule_id": rule_id,
            "reason": reason,
            "context": context,
            "previous_hash": previous_hash,
        }

    def verify_chain(self, entries: list[dict[str, Any]]) -> bool:
        previous_hash = ""
        for entry in entries:
            stored_hash = entry.get("chain_hash", "")
            prev = entry.get("previous_hash", "")

            if prev != previous_hash:
                return False

            hash_input = {k: v for k, v in entry.items() if k != "chain_hash"}
            computed = self.compute_hash(hash_input)
            if computed != stored_hash:
                return False

            previous_hash = stored_hash

        return True
