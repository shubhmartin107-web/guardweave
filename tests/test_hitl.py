
from guardweave.core.enums import ApprovalStatus, Capability, RiskLevel
from guardweave.core.models import ApprovalRequest
from guardweave.hitl.escalation import EscalationHandler


class TestEscalation:
    def test_escalation_timeout(self):
        handler = EscalationHandler()
        req = ApprovalRequest(
            id="test-1",
            agent_id="a1",
            session_id="s1",
            action="exec",
            capability=Capability.SHELL,
            target="/bin/bash",
            risk_score=80,
            risk_level=RiskLevel.HIGH,
            escalation_level=0,
        )
        decision = handler.handle_timeout(req)
        assert decision == ApprovalStatus.ESCALATED

    def test_max_escalation_timeout(self):
        handler = EscalationHandler()
        req = ApprovalRequest(
            id="test-2",
            agent_id="a1",
            session_id="s1",
            action="exec",
            capability=Capability.SHELL,
            target="/bin/bash",
            risk_score=80,
            risk_level=RiskLevel.HIGH,
            escalation_level=3,
        )
        decision = handler.handle_timeout(req)
        assert decision == ApprovalStatus.TIMED_OUT

    def test_timeout_seconds_by_risk(self):
        handler = EscalationHandler()
        assert handler.get_timeout_seconds(RiskLevel.TRIVIAL) == 60
        assert handler.get_timeout_seconds(RiskLevel.LOW) == 120
        assert handler.get_timeout_seconds(RiskLevel.MEDIUM) == 300
        assert handler.get_timeout_seconds(RiskLevel.HIGH) == 600
        assert handler.get_timeout_seconds(RiskLevel.CRITICAL) == 900
