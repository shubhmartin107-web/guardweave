from __future__ import annotations

from typing import Any

POLICY_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "rules"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+(\\.\\d+)?$"},
        "description": {"type": "string"},
        "trust_level": {
            "type": "string",
            "enum": ["sandbox", "low", "medium", "high", "critical"],
        },
        "environment": {
            "type": "string",
            "enum": ["development", "staging", "production"],
        },
        "default_decision": {
            "type": "string",
            "enum": ["allow", "deny", "ask"],
        },
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["match", "decision"],
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                    "match": {
                        "type": "object",
                        "properties": {
                            "capabilities": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "targets": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "agents": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "sessions": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "risk_score_min": {"type": "integer", "minimum": 0, "maximum": 100},
                            "risk_score_max": {"type": "integer", "minimum": 0, "maximum": 100},
                        },
                    },
                    "decision": {
                        "type": "string",
                        "enum": ["allow", "deny", "ask"],
                    },
                    "risk_score_modifier": {"type": "integer"},
                    "reason": {"type": "string"},
                },
            },
        },
    },
}


def validate_policy_dict(data: dict[str, Any]) -> list[str]:

    try:
        import jsonschema
    except ImportError:
        return []

    errors: list[str] = []
    try:
        jsonschema.validate(instance=data, schema=POLICY_JSON_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"Validation error: {e.message}")
    return errors
