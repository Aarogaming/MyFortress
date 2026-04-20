from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schema_validation import validate_envelope_schema, validate_policy_schema

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-fA-F]{16,}$")


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def parse_utc(raw: str | None) -> datetime | None:
    if not raw or not isinstance(raw, str):
        return None
    candidate = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _get_nested(payload: dict[str, Any], dotted_path: str) -> Any:
    cursor: Any = payload
    for segment in dotted_path.split("."):
        if not isinstance(cursor, dict) or segment not in cursor:
            return None
        cursor = cursor[segment]
    return cursor


def _check_digest(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not SHA256_PATTERN.match(value):
        errors.append(f"{field} must be sha256:<hex>, got {value!r}")


def _collect_roles(entries: Any) -> set[str]:
    roles: set[str] = set()
    if isinstance(entries, list):
        for item in entries:
            if isinstance(item, dict) and isinstance(item.get("role"), str):
                roles.add(item["role"])
    return roles


def _collect_verified_attestations(entries: Any) -> set[str]:
    types: set[str] = set()
    if isinstance(entries, list):
        for item in entries:
            if (
                isinstance(item, dict)
                and isinstance(item.get("type"), str)
                and item.get("verified") is True
            ):
                types.add(item["type"])
    return types


def evaluate_gate(
    policy: dict[str, Any],
    envelope: dict[str, Any],
    now_utc: datetime | None = None,
) -> list[str]:
    errors: list[str] = []
    now = now_utc or datetime.now(timezone.utc)

    allowed_workflows = set(policy.get("workflows", []))
    workflow = envelope.get("workflow")
    if workflow not in allowed_workflows:
        errors.append(f"workflow must be one of {sorted(allowed_workflows)}, got {workflow!r}")

    pass0 = policy.get("pass_0", {})
    risk_classes = pass0.get("risk_classes", {})
    risk_class = envelope.get("risk_class")
    risk_policy = risk_classes.get(risk_class)
    if not isinstance(risk_policy, dict):
        errors.append(
            f"risk_class must be one of {sorted(risk_classes.keys())}, got {risk_class!r}"
        )
        return errors

    scope_paths = envelope.get("scope_paths")
    prefixes = policy.get("scope", {}).get("path_allowlist_prefixes", [])
    if not isinstance(scope_paths, list) or not scope_paths:
        errors.append("scope_paths must be a non-empty list")
    else:
        for path in scope_paths:
            if not isinstance(path, str) or not any(path.startswith(prefix) for prefix in prefixes):
                errors.append(f"scope path is outside allowlist: {path!r}")

    target_environment = envelope.get("target_environment")
    allowed_targets = risk_policy.get("allowed_target_environments", [])
    if target_environment not in allowed_targets:
        errors.append(
            f"target_environment {target_environment!r} is not allowed for {risk_class}; "
            f"allowed={allowed_targets}"
        )

    controls = envelope.get("controls")
    if not isinstance(controls, dict):
        errors.append("controls must be an object")
    else:
        for control in risk_policy.get("required_controls", []):
            if controls.get(control) is not True:
                errors.append(f"required control missing or false: {control}")

    approvals = envelope.get("approvals")
    if not isinstance(approvals, list):
        errors.append("approvals must be a list")
        approval_roles: set[str] = set()
    else:
        approval_roles = _collect_roles(approvals)

    min_approvals = risk_policy.get("min_distinct_approvals", 0)
    if len(approval_roles) < min_approvals:
        errors.append(
            f"{risk_class} requires >= {min_approvals} distinct approval roles; "
            f"got {len(approval_roles)} ({sorted(approval_roles)})"
        )
    for required_role in risk_policy.get("required_approval_roles", []):
        if required_role not in approval_roles:
            errors.append(f"required approval role missing: {required_role}")

    pass1 = policy.get("pass_1", {})
    provenance = envelope.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
        provenance = {}
    provenance_rules = pass1.get("provenance_requirements", {})
    for field in provenance_rules.get("required_fields", []):
        value = provenance.get(field)
        if value in (None, "", []):
            errors.append(f"missing provenance field: {field}")
    for field in provenance_rules.get("digest_fields", []):
        _check_digest(provenance.get(field), f"provenance.{field}", errors)

    verified_attestations = _collect_verified_attestations(envelope.get("attestations"))
    required_attestations = provenance_rules.get("attestation_requirements_by_risk", {}).get(
        risk_class, []
    )
    for attestation_type in required_attestations:
        if attestation_type not in verified_attestations:
            errors.append(f"missing verified attestation: {attestation_type}")

    workflow_rules = policy.get("workflow_requirements", {}).get(workflow, {})
    for dotted_path in workflow_rules.get("required_fields", []):
        value = _get_nested(envelope, dotted_path)
        if value in (None, "", []):
            errors.append(f"missing workflow field: {dotted_path}")
    for dotted_path in workflow_rules.get("digest_fields", []):
        _check_digest(_get_nested(envelope, dotted_path), dotted_path, errors)

    if workflow == "maelstrom_runtime_promotion":
        from_stage = _get_nested(envelope, "workflow_metadata.promotion_from")
        to_stage = _get_nested(envelope, "workflow_metadata.promotion_to")
        transition = f"{from_stage}->{to_stage}"
        allowed_transitions = set(workflow_rules.get("allowed_transitions", []))
        if transition not in allowed_transitions:
            errors.append(
                f"maelstrom transition {transition!r} is not allowed; "
                f"allowed={sorted(allowed_transitions)}"
            )

    incident = envelope.get("incident")
    if not isinstance(incident, dict):
        errors.append("incident must be an object")
        incident = {}
    freeze_active = bool(incident.get("freeze_active"))
    override_requested = bool(incident.get("override_requested"))

    override_rule = (
        pass1.get("incident_controls", {}).get("override_rules_by_risk", {}).get(risk_class, {})
    )

    if freeze_active and not override_requested:
        errors.append("incident freeze is active; override_requested must be true")

    if not freeze_active and override_requested:
        errors.append("override_requested must be false when freeze_active is false")

    if freeze_active and override_requested:
        if not override_rule.get("allow_override", False):
            errors.append(f"override not allowed for risk class {risk_class}")

        ticket = incident.get("override_ticket")
        prefix = override_rule.get("ticket_prefix", "")
        if not isinstance(ticket, str) or not ticket.startswith(prefix):
            errors.append(f"override_ticket must start with {prefix!r}")

        reason = incident.get("override_reason", "")
        min_reason_chars = int(override_rule.get("min_reason_chars", 0))
        if not isinstance(reason, str) or len(reason.strip()) < min_reason_chars:
            errors.append(
                f"override_reason must contain at least {min_reason_chars} non-space characters"
            )

        override_roles = set()
        raw_override_roles = incident.get("override_approval_roles")
        if isinstance(raw_override_roles, list):
            override_roles = {
                role for role in raw_override_roles if isinstance(role, str) and role.strip()
            }
        for required_role in override_rule.get("required_roles", []):
            if required_role not in override_roles:
                errors.append(f"override approval role missing: {required_role}")

        requested_at = parse_utc(incident.get("override_requested_at_utc"))
        expires_at = parse_utc(incident.get("override_expires_utc"))
        if requested_at is None:
            errors.append("override_requested_at_utc must be RFC3339 UTC timestamp")
        if expires_at is None:
            errors.append("override_expires_utc must be RFC3339 UTC timestamp")
        if requested_at is not None and expires_at is not None:
            if expires_at <= requested_at:
                errors.append("override_expires_utc must be greater than override_requested_at_utc")
            max_override_minutes = int(override_rule.get("max_override_minutes", 0))
            minutes = (expires_at - requested_at).total_seconds() / 60
            if max_override_minutes > 0 and minutes > max_override_minutes:
                errors.append(
                    f"override window {minutes:.1f}m exceeds max {max_override_minutes}m "
                    f"for {risk_class}"
                )
            if expires_at <= now:
                errors.append("override has expired relative to evaluation time")

    return errors


def evaluate_from_paths(
    policy_path: str | Path,
    envelope_path: str | Path,
    now_utc: datetime | None = None,
) -> list[str]:
    policy = load_json(policy_path)
    envelope = load_json(envelope_path)
    schema_errors = validate_policy_schema(policy)
    schema_errors.extend(validate_envelope_schema(envelope))
    if schema_errors:
        return [f"schema validation failed: {err}" for err in schema_errors]
    return evaluate_gate(policy=policy, envelope=envelope, now_utc=now_utc)
