from __future__ import annotations

import re
from typing import Any


def _is_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return False


def _validate_schema(
    value: Any,
    schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    expected_type = schema.get("type")
    if isinstance(expected_type, str):
        if not _is_type(value, expected_type):
            errors.append(f"{path} expected type {expected_type}, got {type(value).__name__}")
            return

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{path} must be one of {enum_values}, got {value!r}")

    if isinstance(value, str):
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.match(pattern, value) is None:
            errors.append(f"{path} does not match required pattern {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{path} must be >= {minimum}, got {value}")
        maximum = schema.get("maximum")
        if isinstance(maximum, (int, float)) and value > maximum:
            errors.append(f"{path} must be <= {maximum}, got {value}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path} must contain at least {min_items} items")
        max_items = schema.get("maxItems")
        if isinstance(max_items, int) and len(value) > max_items:
            errors.append(f"{path} must contain at most {max_items} items")

        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(value):
                _validate_schema(item, item_schema, f"{path}[{idx}]", errors)

    if isinstance(value, dict):
        min_properties = schema.get("minProperties")
        if isinstance(min_properties, int) and len(value) < min_properties:
            errors.append(f"{path} must contain at least {min_properties} properties")

        required = schema.get("required", [])
        if isinstance(required, list):
            for field in required:
                if isinstance(field, str) and field not in value:
                    errors.append(f"{path}.{field} is required")

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in value and isinstance(child_schema, dict):
                    _validate_schema(value[key], child_schema, f"{path}.{key}", errors)

        additional_properties = schema.get("additionalProperties")
        if additional_properties is False and isinstance(properties, dict):
            allowed = set(properties.keys())
            for key in value:
                if key not in allowed:
                    errors.append(f"{path}.{key} is not allowed")


POLICY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "policy_id",
        "scope",
        "workflows",
        "workflow_requirements",
        "pass_0",
        "pass_1",
        "pass_2",
    ],
    "properties": {
        "policy_id": {"type": "string"},
        "scope": {
            "type": "object",
            "required": ["path_allowlist_prefixes"],
            "properties": {
                "path_allowlist_prefixes": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                }
            },
        },
        "workflows": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
        },
        "workflow_requirements": {"type": "object", "minProperties": 1},
        "pass_0": {
            "type": "object",
            "required": ["risk_classes"],
            "properties": {
                "risk_classes": {"type": "object", "minProperties": 1},
            },
        },
        "pass_1": {
            "type": "object",
            "required": ["provenance_requirements", "incident_controls"],
            "properties": {
                "provenance_requirements": {"type": "object"},
                "incident_controls": {"type": "object"},
            },
        },
        "pass_2": {
            "type": "object",
            "required": ["phase_control", "cp3_enforce_transition_matrix"],
            "properties": {
                "phase_control": {
                    "type": "object",
                    "required": [
                        "active_cycle_phase",
                        "active_rollout_phase",
                        "active_mode",
                        "hard_fail_enabled",
                        "authoritative_sources",
                    ],
                    "properties": {
                        "active_cycle_phase": {"type": "string"},
                        "active_rollout_phase": {"type": "string"},
                        "active_mode": {"type": "string"},
                        "hard_fail_enabled": {"type": "boolean"},
                        "authoritative_sources": {
                            "type": "object",
                            "required": [
                                "policy_path",
                                "evaluator_entrypoint",
                                "evaluator_function",
                            ],
                            "properties": {
                                "policy_path": {"type": "string"},
                                "evaluator_entrypoint": {"type": "string"},
                                "evaluator_function": {"type": "string"},
                            },
                        },
                    },
                },
                "cp3_enforce_transition_matrix": {
                    "type": "object",
                    "required": [
                        "target_rollout_phase",
                        "target_mode",
                        "decision_rule",
                        "criteria",
                    ],
                    "properties": {
                        "target_rollout_phase": {"type": "string"},
                        "target_mode": {"type": "string"},
                        "decision_rule": {"type": "string"},
                        "criteria": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "required": ["criterion_id", "name", "required", "type"],
                                "properties": {
                                    "criterion_id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "required": {"type": "boolean"},
                                    "type": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


ENVELOPE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "cycle_id",
        "workflow",
        "risk_class",
        "target_environment",
        "scope_paths",
        "controls",
        "approvals",
        "provenance",
        "attestations",
        "incident",
        "workflow_metadata",
    ],
    "properties": {
        "cycle_id": {"type": "string"},
        "workflow": {"type": "string"},
        "risk_class": {"type": "string"},
        "target_environment": {"type": "string"},
        "scope_paths": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
        },
        "controls": {"type": "object", "minProperties": 1},
        "approvals": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["role"],
                "properties": {
                    "role": {"type": "string"},
                },
            },
        },
        "provenance": {"type": "object", "minProperties": 1},
        "attestations": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["type", "verified"],
                "properties": {
                    "type": {"type": "string"},
                    "verified": {"type": "boolean"},
                },
            },
        },
        "incident": {
            "type": "object",
            "required": ["freeze_active", "override_requested"],
            "properties": {
                "freeze_active": {"type": "boolean"},
                "override_requested": {"type": "boolean"},
            },
        },
        "workflow_metadata": {"type": "object", "minProperties": 1},
    },
}


CP3_METRICS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["metrics"],
    "properties": {
        "cycle_id": {"type": "string"},
        "generated_utc": {"type": "string"},
        "metrics": {
            "type": "object",
            "required": [
                "false_positive_gate_failures",
                "total_gate_evaluations",
                "approved_overrides",
                "policy_pass_or_valid_override_events",
                "total_promotion_attempts",
                "promotions_with_required_canary_soak_evidence",
                "staging_to_canary_and_canary_to_prod_promotions",
                "open_critical_policy_exceptions",
            ],
            "properties": {
                "false_positive_gate_failures": {"type": "number", "minimum": 0},
                "total_gate_evaluations": {"type": "number", "minimum": 0},
                "approved_overrides": {"type": "number", "minimum": 0},
                "policy_pass_or_valid_override_events": {"type": "number", "minimum": 0},
                "total_promotion_attempts": {"type": "number", "minimum": 0},
                "promotions_with_required_canary_soak_evidence": {"type": "number", "minimum": 0},
                "staging_to_canary_and_canary_to_prod_promotions": {"type": "number", "minimum": 0},
                "open_critical_policy_exceptions": {"type": "number", "minimum": 0},
            },
        },
        "observed_values": {"type": "object"},
    },
}


def validate_policy_schema(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _validate_schema(payload, POLICY_SCHEMA, "policy", errors)
    return errors


def validate_envelope_schema(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _validate_schema(payload, ENVELOPE_SCHEMA, "envelope", errors)
    return errors


def validate_cp3_metrics_schema(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _validate_schema(payload, CP3_METRICS_SCHEMA, "cp3_metrics", errors)
    return errors
