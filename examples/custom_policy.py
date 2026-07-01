"""Example of creating and applying a custom policy programmatically."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardweave.core.enums import Capability, TrustLevel
from guardweave.core.models import ActionContext
from guardweave.engine.evaluator import PolicyEvaluator
from guardweave.engine.policy_parser import load_policy_from_yaml

CUSTOM_POLICY_YAML = """
name: custom-research-policy
version: "1.0"
description: "Custom policy for research agents"
trust_level: medium
environment: development
default_decision: ask
rules:
  - id: allow_web_research
    description: "Allow web research via HTTP"
    match:
      capabilities: ["network:http"]
      targets: ["https://api.duckduckgo.com/*", "https://en.wikipedia.org/*"]
    decision: allow
    reason: "Web research is permitted"

  - id: deny_write_system
    description: "Block writes to system directories"
    match:
      capabilities: ["file:write"]
      targets: ["/etc/*", "/usr/*", "/bin/*"]
    decision: deny
    reason: "Writing to system directories is prohibited"

  - id: ask_code_exec
    description: "Require approval for code execution"
    match:
      capabilities: ["code:exec", "shell"]
    decision: ask
    reason: "Code execution requires human oversight"
"""


async def main():
    # Load the custom policy from YAML
    policy = load_policy_from_yaml(CUSTOM_POLICY_YAML)
    print(f"Policy: {policy.name} v{policy.version}")
    print(f"Rules: {len(policy.rules)}")

    # Create evaluator with this policy
    evaluator = PolicyEvaluator([policy])

    # Test various actions
    test_cases = [
        ("HTTP research", Capability.NETWORK_HTTP, "https://en.wikipedia.org/wiki/AI", TrustLevel.MEDIUM),
        ("System write", Capability.FILE_WRITE, "/etc/hosts", TrustLevel.MEDIUM),
        ("Code execution", Capability.CODE_EXEC, "python3 script.py", TrustLevel.MEDIUM),
        ("File read", Capability.FILE_READ, "/tmp/data.txt", TrustLevel.MEDIUM),
        ("Dangerous HTTP", Capability.NETWORK_HTTP, "https://unknown-site.com/hack", TrustLevel.MEDIUM),
    ]

    for name, capability, target, trust in test_cases:
        ctx = ActionContext(
            agent_id="research-agent",
            session_id="session-1",
            action=name,
            capability=capability,
            target=target,
            trust_level=trust,
            environment="development",
        )
        result = evaluator.evaluate(ctx, policy=policy)
        print(f"  {name:25s} -> {result.decision.value:6s} (risk={result.risk_score:2d}) [{result.reason[:40]}]")


if __name__ == "__main__":
    asyncio.run(main())
