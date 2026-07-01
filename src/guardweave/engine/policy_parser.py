from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from guardweave.core.enums import Decision
from guardweave.core.exceptions import PolicyParseError
from guardweave.core.models import Policy, Rule, RuleMatch


def load_policy_from_yaml(yaml_str: str, source: str = "<string>") -> Policy:
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise PolicyParseError(f"YAML parse error in {source}: {e}")

    if not isinstance(data, dict):
        raise PolicyParseError(f"Policy in {source} must be a mapping")

    return _parse_policy_dict(data)


def load_policy_from_file(path: str | Path) -> Policy:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    content = path.read_text()
    return load_policy_from_yaml(content, source=str(path))


def _parse_policy_dict(data: dict[str, Any]) -> Policy:
    policy = Policy(
        name=data.get("name", "unnamed"),
        version=str(data.get("version", "1.0")),
        description=data.get("description", ""),
        trust_level=data.get("trust_level", "medium"),
        environment=data.get("environment", "development"),
        default_decision=_parse_decision(data.get("default_decision", "ask")),
    )

    rules_data = data.get("rules", [])
    for i, rule_data in enumerate(rules_data):
        if not isinstance(rule_data, dict):
            raise PolicyParseError(f"Rule at index {i} must be a mapping")

        match_data = rule_data.get("match", {})
        if not isinstance(match_data, dict):
            raise PolicyParseError(f"Rule {i} 'match' must be a mapping")

        rule = Rule(
            id=rule_data.get("id", f"rule_{i}"),
            description=rule_data.get("description", ""),
            match=RuleMatch(**match_data),
            decision=_parse_decision(rule_data.get("decision", "ask")),
            risk_score_modifier=rule_data.get("risk_score_modifier", 0),
            reason=rule_data.get("reason", ""),
        )
        policy.rules.append(rule)

    return policy


def _parse_decision(value: str) -> Decision:
    try:
        return Decision(value.lower())
    except ValueError:
        raise PolicyParseError(f"Invalid decision value: {value}. Must be one of: allow, deny, ask")
