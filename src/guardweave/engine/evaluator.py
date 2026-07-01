from __future__ import annotations

import fnmatch
import logging

from guardweave.core.enums import Decision, RiskLevel, TrustLevel
from guardweave.core.exceptions import PolicyNotFoundError
from guardweave.core.models import ActionContext, Policy, PolicyEvaluationResult, Rule

logger = logging.getLogger("guardweave.engine.evaluator")


class PolicyEvaluator:
    def __init__(self, policies: list[Policy] | None = None):
        self._policies: dict[str, Policy] = {}
        self._policies_by_name: dict[str, Policy] = {}
        if policies:
            for p in policies:
                self.add_policy(p)

    def add_policy(self, policy: Policy) -> None:
        self._policies[policy.id] = policy
        self._policies_by_name[policy.name] = policy

    def remove_policy(self, policy_id: str) -> None:
        policy = self._policies.pop(policy_id, None)
        if policy:
            self._policies_by_name.pop(policy.name, None)

    def get_policy(self, policy_id: str | None = None, policy_name: str | None = None) -> Policy | None:
        if policy_id:
            return self._policies.get(policy_id)
        if policy_name:
            return self._policies_by_name.get(policy_name)
        # Return first active policy
        for p in self._policies.values():
            if p.active:
                return p
        return None

    def evaluate_batch(
        self,
        contexts: list[ActionContext],
        policy: Policy | None = None,
    ) -> list[PolicyEvaluationResult]:
        return [self.evaluate(ctx, policy=policy) for ctx in contexts]

    def get_policy_version_history(self, policy_id: str) -> list[str]:
        policy = self._policies.get(policy_id)
        if not policy:
            return []
        return [f"{policy.name} v{policy.version}"]

    def evaluate(
        self,
        context: ActionContext,
        policy: Policy | None = None,
    ) -> PolicyEvaluationResult:
        if policy is None:
            policy = self._find_best_policy(context)

        if policy is None:
            raise PolicyNotFoundError("No active policy found for evaluation")

        matched_rule = self._find_matching_rule(policy, context)
        if matched_rule:
            decision = matched_rule.decision
            risk_score_modifier = matched_rule.risk_score_modifier
            reason = matched_rule.reason
        else:
            decision = policy.default_decision
            risk_score_modifier = 0
            reason = f"No matching rule; using default decision: {decision.value}"

        from guardweave.engine.risk_scorer import RiskScorer

        risk_score, risk_level = RiskScorer().calculate(context)
        risk_score = max(0, min(100, risk_score + risk_score_modifier))
        risk_level = self._score_to_level(risk_score)

        return PolicyEvaluationResult(
            decision=decision,
            risk_score=risk_score,
            risk_level=risk_level,
            matched_rule=matched_rule,
            policy_id=policy.id,
            reason=reason,
            requires_approval=(decision == Decision.ASK),
            context=context,
        )

    def _find_best_policy(self, context: ActionContext) -> Policy | None:
        candidates = []
        for policy in self._policies.values():
            if not policy.active:
                continue
            if policy.environment != context.environment:
                continue
            if (
                TrustLevel(policy.trust_level).value
                != context.trust_level.value
            ):
                continue
            candidates.append(policy)

        if not candidates:
            for policy in self._policies.values():
                if policy.active:
                    return policy

        return candidates[0] if candidates else None

    def _find_matching_rule(self, policy: Policy, context: ActionContext) -> Rule | None:
        for rule in policy.rules:
            if self._rule_matches(rule, context):
                return rule
        return None

    def _rule_matches(self, rule: Rule, context: ActionContext) -> bool:
        match = rule.match

        if match.capabilities and context.capability not in match.capabilities and context.capability.value not in match.capabilities:
            return False

        if match.targets and not any(fnmatch.fnmatch(context.target, t) for t in match.targets):
            return False

        if match.agents and context.agent_id not in match.agents:
            return False

        if match.sessions and context.session_id not in match.sessions:
            return False
        return True

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
