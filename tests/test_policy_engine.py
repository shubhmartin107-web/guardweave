from guardweave.core.enums import Capability, Decision, RiskLevel, TrustLevel
from guardweave.core.models import ActionContext, Policy, Rule, RuleMatch
from guardweave.engine.evaluator import PolicyEvaluator
from guardweave.engine.policy_parser import load_policy_from_yaml
from guardweave.engine.risk_scorer import RiskScorer


def make_context(
    action: str = "test",
    capability: str = "file:read",
    target: str = "/tmp/test.txt",
    trust: str = "medium",
    env: str = "development",
) -> ActionContext:
    return ActionContext(
        agent_id="test-agent",
        session_id="test-session",
        action=action,
        capability=Capability(capability),
        target=target,
        trust_level=TrustLevel(trust),
        environment=env,
    )


def test_policy_allow():
    policy = Policy(
        name="test-allow",
        default_decision=Decision.ASK,
        rules=[
            Rule(
                id="r1",
                match=RuleMatch(capabilities=[Capability.FILE_READ]),
                decision=Decision.ALLOW,
            )
        ],
    )
    evaluator = PolicyEvaluator([policy])
    ctx = make_context(capability="file:read")
    result = evaluator.evaluate(ctx, policy=policy)
    assert result.decision == Decision.ALLOW


def test_policy_deny():
    policy = Policy(
        name="test-deny",
        default_decision=Decision.ALLOW,
        rules=[
            Rule(
                id="r1",
                match=RuleMatch(capabilities=[Capability.SHELL]),
                decision=Decision.DENY,
            )
        ],
    )
    evaluator = PolicyEvaluator([policy])
    ctx = make_context(action="exec", capability="shell", target="/bin/bash")
    result = evaluator.evaluate(ctx, policy=policy)
    assert result.decision == Decision.DENY


def test_policy_default_decision():
    policy = Policy(
        name="test-default",
        default_decision=Decision.ASK,
        rules=[],
    )
    evaluator = PolicyEvaluator([policy])
    ctx = make_context()
    result = evaluator.evaluate(ctx, policy=policy)
    assert result.decision == Decision.ASK
    assert result.requires_approval is True


def test_risk_scorer():
    scorer = RiskScorer()
    ctx = make_context(capability="shell", target="/etc/shadow")
    score, level = scorer.calculate(ctx)
    assert score >= 80  # shell base (80) + sensitive target (20)
    assert level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    ctx2 = make_context(capability="file:read", target="/tmp/test.txt")
    score2, level2 = scorer.calculate(ctx2)
    assert score2 == 20  # file:read base (10) * medium multiplier (1.0) + tmp modifier (10)
    assert level2 == RiskLevel.LOW


def test_target_matching():
    policy = Policy(
        name="test-target",
        default_decision=Decision.ALLOW,
        rules=[
            Rule(
                id="r1",
                match=RuleMatch(
                    capabilities=[Capability.FILE_WRITE],
                    targets=["/etc/*", "/usr/*"],
                ),
                decision=Decision.DENY,
            )
        ],
    )
    evaluator = PolicyEvaluator([policy])
    ctx = make_context(capability="file:write", target="/etc/passwd")
    result = evaluator.evaluate(ctx, policy=policy)
    assert result.decision == Decision.DENY

    ctx2 = make_context(capability="file:write", target="/tmp/test.txt")
    result2 = evaluator.evaluate(ctx2, policy=policy)
    assert result2.decision == Decision.ALLOW  # default decision


def test_yaml_policy_parsing():
    yaml = """
name: test-yaml
version: "1.0"
trust_level: medium
environment: development
default_decision: deny
rules:
  - id: allow_reads
    match:
      capabilities: ["file:read"]
    decision: allow
    reason: "Reads are safe"
"""
    policy = load_policy_from_yaml(yaml)
    assert policy.name == "test-yaml"
    assert len(policy.rules) == 1
    assert policy.rules[0].id == "allow_reads"
    assert policy.rules[0].decision == Decision.ALLOW


def test_multiple_policies():
    dev = Policy(name="dev", environment="development", default_decision=Decision.ALLOW)
    prod = Policy(name="prod", environment="production", default_decision=Decision.DENY)

    evaluator = PolicyEvaluator([dev, prod])
    ctx = make_context(env="development")
    result = evaluator.evaluate(ctx)
    assert result.decision == Decision.ALLOW

    ctx2 = make_context(env="production")
    result2 = evaluator.evaluate(ctx2)
    assert result2.decision == Decision.DENY
