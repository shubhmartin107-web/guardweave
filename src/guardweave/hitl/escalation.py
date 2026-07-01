from __future__ import annotations

from guardweave.core.enums import ApprovalStatus, RiskLevel
from guardweave.core.models import ApprovalRequest

# Max escalation levels per risk level
MAX_ESCALATION: dict[RiskLevel, int] = {
    RiskLevel.TRIVIAL: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 3,
}

# Timeout action per escalation level
TIMEOUT_ACTIONS: dict[int, ApprovalStatus] = {
    0: ApprovalStatus.DENIED,
    1: ApprovalStatus.ESCALATED,
    2: ApprovalStatus.ESCALATED,
    3: ApprovalStatus.TIMED_OUT,
}


class EscalationHandler:
    def handle_timeout(self, req: ApprovalRequest) -> ApprovalStatus:
        max_level = MAX_ESCALATION.get(req.risk_level, 1)

        if req.escalation_level < max_level:
            return ApprovalStatus.ESCALATED
        else:
            return TIMEOUT_ACTIONS.get(req.escalation_level, ApprovalStatus.DENIED)

    def get_timeout_seconds(self, risk_level: RiskLevel) -> int:
        timeout_map: dict[RiskLevel, int] = {
            RiskLevel.TRIVIAL: 60,
            RiskLevel.LOW: 120,
            RiskLevel.MEDIUM: 300,
            RiskLevel.HIGH: 600,
            RiskLevel.CRITICAL: 900,
        }
        return timeout_map.get(risk_level, 300)
