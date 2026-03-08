from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gate_eval import load_json
from .schema_validation import validate_cp3_metrics_schema, validate_policy_schema


def _get_nested(payload: dict[str, Any], dotted_path: str) -> Any:
    cursor: Any = payload
    for segment in dotted_path.split("."):
        if not isinstance(cursor, dict) or segment not in cursor:
            return None
        cursor = cursor[segment]
    return cursor


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _get_metric(payload: dict[str, Any], key: str) -> Any:
    if key in payload:
        return payload[key]
    metrics = payload.get("metrics")
    if isinstance(metrics, dict):
        return metrics.get(key)
    return None


def evaluate_cp3_readiness(
    policy: dict[str, Any],
    metrics_payload: dict[str, Any],
    require_observed_exact_match_fields: bool = False,
) -> dict[str, Any]:
    pass2 = policy.get("pass_2", {})
    matrix = pass2.get("cp3_enforce_transition_matrix", {})
    criteria = matrix.get("criteria", [])
    if not isinstance(criteria, list):
        raise ValueError("pass_2.cp3_enforce_transition_matrix.criteria must be a list")

    observed_values = metrics_payload.get("observed_values")
    if not isinstance(observed_values, dict):
        observed_values = {}

    results: list[dict[str, Any]] = []
    failures: list[str] = []

    for raw_criterion in criteria:
        if not isinstance(raw_criterion, dict):
            failures.append("criterion entry must be an object")
            continue

        criterion_id = str(raw_criterion.get("criterion_id", "UNKNOWN"))
        name = str(raw_criterion.get("name", "unnamed"))
        criterion_type = raw_criterion.get("type")
        required = bool(raw_criterion.get("required", False))

        passed = False
        message = "criterion not evaluated"
        observed: dict[str, Any] = {}

        if criterion_type == "exact_match":
            expected_values = raw_criterion.get("expected_values", {})
            if not isinstance(expected_values, dict):
                message = "expected_values must be an object"
            else:
                mismatches: list[str] = []
                for path, expected in expected_values.items():
                    actual_policy = _get_nested(pass2, str(path))
                    observed[f"policy:{path}"] = actual_policy
                    if actual_policy != expected:
                        mismatches.append(f"{path} policy={actual_policy!r} expected={expected!r}")

                    if path in observed_values:
                        actual_observed = observed_values[path]
                        observed[f"observed:{path}"] = actual_observed
                        if actual_observed != expected:
                            mismatches.append(
                                f"{path} observed={actual_observed!r} expected={expected!r}"
                            )
                    elif require_observed_exact_match_fields:
                        mismatches.append(f"{path} missing in observed_values")

                if mismatches:
                    message = "; ".join(mismatches)
                else:
                    passed = True
                    message = "all expected values matched"

        elif criterion_type in {"ratio_max", "ratio_min"}:
            numerator_key = raw_criterion.get("metric_numerator")
            denominator_key = raw_criterion.get("metric_denominator")
            numerator = _as_number(_get_metric(metrics_payload, str(numerator_key)))
            denominator = _as_number(_get_metric(metrics_payload, str(denominator_key)))
            observed["metric_numerator"] = numerator
            observed["metric_denominator"] = denominator

            if numerator is None or denominator is None:
                message = "missing numeric numerator/denominator metrics"
            elif denominator <= 0:
                message = f"denominator must be > 0, got {denominator}"
            else:
                ratio = numerator / denominator
                observed["ratio"] = ratio
                if criterion_type == "ratio_max":
                    threshold = _as_number(raw_criterion.get("max_value"))
                    observed["max_value"] = threshold
                    if threshold is None:
                        message = "max_value must be numeric"
                    elif ratio <= threshold:
                        passed = True
                        message = f"{ratio:.6f} <= {threshold:.6f}"
                    else:
                        message = f"{ratio:.6f} > {threshold:.6f}"
                else:
                    threshold = _as_number(raw_criterion.get("min_value"))
                    observed["min_value"] = threshold
                    if threshold is None:
                        message = "min_value must be numeric"
                    elif ratio >= threshold:
                        passed = True
                        message = f"{ratio:.6f} >= {threshold:.6f}"
                    else:
                        message = f"{ratio:.6f} < {threshold:.6f}"

        elif criterion_type == "count_max":
            metric_name = str(raw_criterion.get("metric_name"))
            value = _as_number(_get_metric(metrics_payload, metric_name))
            max_value = _as_number(raw_criterion.get("max_value"))
            observed["metric_value"] = value
            observed["max_value"] = max_value

            if value is None or max_value is None:
                message = "count_max requires numeric metric_name and max_value"
            elif value <= max_value:
                passed = True
                message = f"{value:.6f} <= {max_value:.6f}"
            else:
                message = f"{value:.6f} > {max_value:.6f}"

        else:
            message = f"unsupported criterion type: {criterion_type!r}"

        result = {
            "criterion_id": criterion_id,
            "name": name,
            "required": required,
            "type": criterion_type,
            "passed": passed,
            "message": message,
            "observed": observed,
        }
        results.append(result)

        if required and not passed:
            failures.append(f"{criterion_id}: {message}")

    decision_rule = matrix.get("decision_rule", "all_criteria_required")
    ready = len(failures) == 0
    evaluated_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "ready": ready,
        "decision_rule": decision_rule,
        "target_rollout_phase": matrix.get("target_rollout_phase"),
        "target_mode": matrix.get("target_mode"),
        "evaluated_utc": evaluated_utc,
        "criteria_results": results,
        "failures": failures,
    }


def evaluate_cp3_readiness_from_paths(
    policy_path: str | Path,
    metrics_path: str | Path,
    require_observed_exact_match_fields: bool = False,
) -> dict[str, Any]:
    policy = load_json(policy_path)
    metrics_payload = load_json(metrics_path)
    schema_errors = validate_policy_schema(policy)
    schema_errors.extend(validate_cp3_metrics_schema(metrics_payload))
    if schema_errors:
        raise ValueError("; ".join(schema_errors))
    return evaluate_cp3_readiness(
        policy=policy,
        metrics_payload=metrics_payload,
        require_observed_exact_match_fields=require_observed_exact_match_fields,
    )
