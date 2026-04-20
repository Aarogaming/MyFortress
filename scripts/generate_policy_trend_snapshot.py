import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _to_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a versioned policy trend snapshot from CP3 metrics/report artifacts."
    )
    parser.add_argument("--metrics", required=True, help="Path to CP3 metrics JSON")
    parser.add_argument(
        "--report",
        default=None,
        help="Optional path to CP3 readiness report JSON",
    )
    parser.add_argument(
        "--snapshot-id",
        default=None,
        help="Optional snapshot identifier (default: UTC timestamp)",
    )
    parser.add_argument("--output", required=True, help="Output path for trend snapshot JSON")
    args = parser.parse_args()

    metrics_payload = _load_json(Path(args.metrics))
    metrics = metrics_payload.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("metrics payload must include a 'metrics' object")

    false_positives = _to_number(metrics.get("false_positive_gate_failures"))
    total_evaluations = _to_number(metrics.get("total_gate_evaluations"))
    approved_overrides = _to_number(metrics.get("approved_overrides"))
    open_exceptions = _to_number(metrics.get("open_critical_policy_exceptions"))

    report_payload: dict[str, Any] = {}
    if args.report:
        report_payload = _load_json(Path(args.report))
    report_ready = report_payload.get("ready")
    report_failures = report_payload.get("failures")
    if not isinstance(report_failures, list):
        report_failures = []

    now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot_id = args.snapshot_id or now_utc

    snapshot = {
        "schema_version": "policy_trend_snapshot_v1",
        "snapshot_id": snapshot_id,
        "generated_utc": now_utc,
        "cycle_id": metrics_payload.get("cycle_id"),
        "inputs": {
            "metrics_path": args.metrics,
            "report_path": args.report,
        },
        "trend_metrics": {
            "false_positive_gate_failures": false_positives,
            "total_gate_evaluations": total_evaluations,
            "false_positive_rate": _ratio(false_positives, total_evaluations),
            "approved_overrides": approved_overrides,
            "override_rate": _ratio(approved_overrides, total_evaluations),
            "open_critical_policy_exceptions": open_exceptions,
        },
        "cp3_readiness": {
            "ready": report_ready,
            "failure_count": len(report_failures),
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    print(f"POLICY_TREND_SNAPSHOT_WRITTEN {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
