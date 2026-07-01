from __future__ import annotations

from guardweave.core.enums import Capability, RiskLevel, TrustLevel
from guardweave.core.models import ActionContext

# Base risk scores for each capability
CAPABILITY_BASE_RISK: dict[Capability, int] = {
    Capability.FILE_READ: 10,
    Capability.FILE_WRITE: 25,
    Capability.FILE_DELETE: 50,
    Capability.FILE_EXECUTE: 60,
    Capability.NETWORK_HTTP: 15,
    Capability.NETWORK_RAW: 45,
    Capability.CODE_EXEC: 70,
    Capability.CODE_EVAL: 65,
    Capability.SHELL: 80,
    Capability.API_CALL: 20,
    Capability.DB_READ: 15,
    Capability.DB_WRITE: 35,
    Capability.DB_EXECUTE: 55,
    Capability.SECRETS_ACCESS: 75,
    Capability.IDENTITY_IMPERSONATE: 90,
    Capability.DATA_EXFILTRATE: 85,
    Capability.AGENT_SPAWN: 60,
    Capability.AGENT_TERMINATE: 70,
    Capability.POLICY_MODIFY: 85,
    Capability.AUDIT_MODIFY: 90,
}

# Trust level multipliers (lower trust = higher risk multiplier)
TRUST_MULTIPLIERS: dict[TrustLevel, float] = {
    TrustLevel.SANDBOX: 1.5,
    TrustLevel.LOW: 1.3,
    TrustLevel.MEDIUM: 1.0,
    TrustLevel.HIGH: 0.7,
    TrustLevel.CRITICAL: 0.4,
}

SENSITIVE_TARGET_KEYWORDS = [
    "password", "secret", "key", "token", "credential", "certificate",
    ".env", "id_rsa", "aws-", "gcp-", "ssh", "pem",
    "/etc/shadow", "/etc/passwd", "/etc/ssl",
    "database_url", "connection_string",
]


class RiskScorer:
    def calculate(self, context: ActionContext) -> tuple[int, RiskLevel]:
        score = self._base_score(context)
        score = self._apply_trust_multiplier(score, context.trust_level)
        score = self._apply_target_modifier(score, context.target)
        score = max(0, min(100, score))
        level = self._score_to_level(score)
        return score, level

    def _base_score(self, context: ActionContext) -> int:
        return CAPABILITY_BASE_RISK.get(context.capability, 30)

    def _apply_trust_multiplier(self, score: int, trust_level: TrustLevel) -> int:
        multiplier = TRUST_MULTIPLIERS.get(trust_level, 1.0)
        return int(score * multiplier)

    def _apply_target_modifier(self, score: int, target: str) -> int:
        target_lower = target.lower()
        for keyword in SENSITIVE_TARGET_KEYWORDS:
            if keyword in target_lower:
                score += 20
                break
        if target.startswith("/") or target.startswith("~"):
            score += 10
        return score

    def _score_to_level(self, score: int) -> RiskLevel:
        if score < 10:
            return RiskLevel.TRIVIAL
        elif score < 30:
            return RiskLevel.LOW
        elif score < 50:
            return RiskLevel.MEDIUM
        elif score < 75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
