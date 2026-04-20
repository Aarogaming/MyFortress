import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _require_type(payload: dict[str, Any], key: str, expected: type, errors: list[str], label: str) -> Any:
    value = payload.get(key)
    if not isinstance(value, expected):
        errors.append(f"{label}.{key} expected {expected.__name__}, got {type(value).__name__}")
        return None
    return value


def _validate_cp3_report(path: Path, errors: list[str]) -> None:
    try:
        payload = _load_json(path)
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return

    _require_type(payload, "ready", bool, errors, str(path))
    _require_type(payload, "decision_rule", str, errors, str(path))
    _require_type(payload, "target_rollout_phase", str, errors, str(path))
    _require_type(payload, "target_mode", str, errors, str(path))
    criteria_results = _require_type(payload, "criteria_results", list, errors, str(path))
    failures = _require_type(payload, "failures", list, errors, str(path))
    if failures is not None:
        for idx, failure in enumerate(failures):
            if not isinstance(failure, str):
                errors.append(f"{path}.failures[{idx}] expected str, got {type(failure).__name__}")

    if criteria_results is None:
        return
    for idx, criterion in enumerate(criteria_results):
        if not isinstance(criterion, dict):
            errors.append(f"{path}.criteria_results[{idx}] expected dict, got {type(criterion).__name__}")
            continue
        for field, expected_type in {
            "criterion_id": str,
            "name": str,
            "required": bool,
            "passed": bool,
            "message": str,
        }.items():
            value = criterion.get(field)
            if not isinstance(value, expected_type):
                errors.append(
                    f"{path}.criteria_results[{idx}].{field} expected {expected_type.__name__}, got {type(value).__name__}"
                )


def _validate_trend_snapshot(path: Path, errors: list[str]) -> None:
    try:
        payload = _load_json(path)
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return

    schema_version = payload.get("schema_version")
    if schema_version != "policy_trend_snapshot_v1":
        errors.append(f"{path}.schema_version expected 'policy_trend_snapshot_v1', got {schema_version!r}")

    _require_type(payload, "snapshot_id", str, errors, str(path))
    _require_type(payload, "generated_utc", str, errors, str(path))

    trend_metrics = _require_type(payload, "trend_metrics", dict, errors, str(path))
    if trend_metrics is not None:
        for field in [
            "false_positive_gate_failures",
            "total_gate_evaluations",
            "approved_overrides",
            "open_critical_policy_exceptions",
        ]:
            value = trend_metrics.get(field)
            if not isinstance(value, (int, float)):
                errors.append(f"{path}.trend_metrics.{field} expected number, got {type(value).__name__}")

    cp3_readiness = _require_type(payload, "cp3_readiness", dict, errors, str(path))
    if cp3_readiness is not None:
        ready_value = cp3_readiness.get("ready")
        if ready_value is not None and not isinstance(ready_value, bool):
            errors.append(f"{path}.cp3_readiness.ready expected bool|null, got {type(ready_value).__name__}")
        failure_count = cp3_readiness.get("failure_count")
        if not isinstance(failure_count, int):
            errors.append(
                f"{path}.cp3_readiness.failure_count expected int, got {type(failure_count).__name__}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate shape of generated policy artifacts (CP3 report + trend snapshots)."
    )
    parser.add_argument(
        "--cp3-report",
        required=True,
        help="Path to CP3 readiness report JSON",
    )
    parser.add_argument(
        "--trend-glob",
        required=True,
        help="Glob pattern for trend snapshot JSON files (e.g. artifacts/ci/policy_trend_*.json)",
    )
    args = parser.parse_args()

    errors: list[str] = []
    cp3_report_path = Path(args.cp3_report)
    _validate_cp3_report(cp3_report_path, errors)

    trend_matches = [Path(path) for path in sorted(glob.glob(args.trend_glob))]
    if not trend_matches:
        errors.append(f"no files matched trend glob: {args.trend_glob}")
    for trend_path in trend_matches:
        _validate_trend_snapshot(trend_path, errors)

    if errors:
        sys.stderr.write("GENERATED_ARTIFACT_SHAPE_FAIL\n")
        for error in errors:
            sys.stderr.write(f"- {error}\n")
        return 2

    print("GENERATED_ARTIFACT_SHAPE_PASS")
    print(f"cp3_report={cp3_report_path}")
    print(f"trend_files={len(trend_matches)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
