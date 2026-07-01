"""Integration tests for GuardWeave end-to-end workflows."""

import os

import pytest

from guardweave.core.enums import Capability, Decision, RiskLevel, TrustLevel
from guardweave.core.models import ActionContext, Policy, Rule, RuleMatch
from guardweave.engine.evaluator import PolicyEvaluator
from guardweave.engine.policy_parser import load_policy_from_yaml
from guardweave.engine.risk_scorer import RiskScorer


@pytest.fixture(autouse=True)
def setup_test_env():
    os.environ["GUARDWEAVE_ENV"] = "test"
    yield


class TestEndToEnd:
    def test_full_evaluation_flow(self):
        """Policy evaluation end-to-end with allow, deny, ask"""
        policy = Policy(
            name="e2e",
            default_decision=Decision.ASK,
            rules=[
                Rule(id="r1", match=RuleMatch(capabilities=[Capability.FILE_READ]), decision=Decision.ALLOW),
                Rule(id="r2", match=RuleMatch(capabilities=[Capability.SECRETS_ACCESS]), decision=Decision.DENY),
                Rule(id="r3", match=RuleMatch(capabilities=[Capability.SHELL]), decision=Decision.ASK),
            ],
        )
        evaluator = PolicyEvaluator([policy])

        ctx = ActionContext(agent_id="a1", session_id="s1", action="read", capability=Capability.FILE_READ, target="/tmp/x.txt")
        r = evaluator.evaluate(ctx)
        assert r.decision == Decision.ALLOW
        assert not r.requires_approval

        ctx2 = ActionContext(agent_id="a1", session_id="s1", action="get_secret", capability=Capability.SECRETS_ACCESS, target="/etc/secret")
        r2 = evaluator.evaluate(ctx2)
        assert r2.decision == Decision.DENY

        ctx3 = ActionContext(agent_id="a1", session_id="s1", action="exec", capability=Capability.SHELL, target="/bin/bash")
        r3 = evaluator.evaluate(ctx3)
        assert r3.decision == Decision.ASK
        assert r3.requires_approval

    def test_batch_evaluation(self):
        policy = Policy(name="batch", default_decision=Decision.ALLOW)
        evaluator = PolicyEvaluator([policy])

        contexts = [
            ActionContext(agent_id="a1", session_id="s1", action="r1", capability=Capability.FILE_READ, target="/tmp/1.txt"),
            ActionContext(agent_id="a1", session_id="s1", action="r2", capability=Capability.FILE_READ, target="/tmp/2.txt"),
        ]
        results = evaluator.evaluate_batch(contexts)
        assert len(results) == 2
        assert all(r.decision == Decision.ALLOW for r in results)

    def test_risk_scoring_matrix(self):
        scorer = RiskScorer()
        cases = [
            (Capability.FILE_READ, TrustLevel.HIGH, "/tmp/x.txt", 17, RiskLevel.LOW),
            (Capability.FILE_READ, TrustLevel.MEDIUM, "/tmp/x.txt", 20, RiskLevel.LOW),
            (Capability.SHELL, TrustLevel.MEDIUM, "/bin/bash", 90, RiskLevel.CRITICAL),
            (Capability.SECRETS_ACCESS, TrustLevel.MEDIUM, "/etc/ssl/key.pem", 100, RiskLevel.CRITICAL),
            (Capability.FILE_WRITE, TrustLevel.LOW, "/etc/config.yaml", 42, RiskLevel.MEDIUM),
        ]
        for cap, trust, target, expected_score, expected_level in cases:
            ctx = ActionContext(agent_id="a", session_id="s", action="test", capability=cap, target=target, trust_level=trust)
            score, level = scorer.calculate(ctx)
            assert score == expected_score, f"{cap} score: expected {expected_score}, got {score}"
            assert level == expected_level, f"{cap} level: expected {expected_level}, got {level}"

    def test_yaml_policy_complex(self):
        yaml = """
name: complex-policy
version: "2.0"
description: "A complex policy for testing"
trust_level: high
environment: staging
default_decision: allow
rules:
  - id: allow_api_read
    description: "Allow API GET requests"
    match:
      capabilities: ["api:call"]
      targets: ["https://api.example.com/*"]
    decision: allow
    reason: "API access permitted"

  - id: deny_db_write
    description: "Block database writes"
    match:
      capabilities: ["db:write", "db:execute"]
    decision: deny
    reason: "DB writes require production policy"

  - id: ask_network_raw
    description: "Require approval for raw network"
    match:
      capabilities: ["network:raw"]
    decision: ask
    reason: "Raw network access needs approval"
"""
        policy = load_policy_from_yaml(yaml)
        assert policy.name == "complex-policy"
        assert policy.version == "2.0"
        assert len(policy.rules) == 3

        evaluator = PolicyEvaluator([policy])

        ctx = ActionContext(agent_id="a", session_id="s", action="api_call", capability=Capability.API_CALL, target="https://api.example.com/data")
        r = evaluator.evaluate(ctx)
        assert r.decision == Decision.ALLOW

        ctx2 = ActionContext(agent_id="a", session_id="s", action="db_write", capability=Capability.DB_WRITE, target="my_table")
        r2 = evaluator.evaluate(ctx2)
        assert r2.decision == Decision.DENY

        ctx3 = ActionContext(agent_id="a", session_id="s", action="raw", capability=Capability.NETWORK_RAW, target="0.0.0.0")
        r3 = evaluator.evaluate(ctx3)
        assert r3.decision == Decision.ASK
