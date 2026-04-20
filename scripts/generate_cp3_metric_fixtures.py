import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _base_payload() -> dict[str, Any]:
    return {
        "cycle_id": "CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15",
        "generated_utc": "2026-02-15T12:00:00Z",
        "metrics": {
            "false_positive_gate_failures": 0,
            "total_gate_evaluations": 120,
            "approved_overrides": 4,
            "policy_pass_or_valid_override_events": 72,
            "total_promotion_attempts": 72,
            "promotions_with_required_canary_soak_evidence": 18,
            "staging_to_canary_and_canary_to_prod_promotions": 18,
            "open_critical_policy_exceptions": 0,
        },
        "observed_values": {
            "phase_control.authoritative_sources.policy_path": "docs/policy/JANUS_GATE_POLICY_V1.json",
            "phase_control.authoritative_sources.evaluator_entrypoint": "scripts/evaluate_policy_gate.py",
            "phase_control.authoritative_sources.evaluator_function": "gateway.policy.gate_eval.evaluate_gate",
        },
    }


def _apply_overrides(payload: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    mutated = deepcopy(payload)
    for dotted_path, value in updates.items():
        cursor: Any = mutated
        parts = dotted_path.split(".")
        for part in parts[:-1]:
            if not isinstance(cursor, dict):
                raise ValueError(f"Cannot apply override at {dotted_path!r}")
            cursor = cursor.setdefault(part, {})
        if not isinstance(cursor, dict):
            raise ValueError(f"Cannot apply override at {dotted_path!r}")
        cursor[parts[-1]] = value
    return mutated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate CP3 metrics pass/fail fixture JSON files in artifacts/policy."
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/policy",
        help="Directory to write fixture JSON files (default: artifacts/policy)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base = _base_payload()
    _write_json(output_dir / "cp3_readiness_metrics_example.json", base)

    fail_cases = {
        "cp3_readiness_metrics_fail_cp3_01.json": {
            "observed_values": {
                "phase_control.authoritative_sources.policy_path": "docs/policy/JANUS_GATE_POLICY_V2.json",
                "phase_control.authoritative_sources.evaluator_entrypoint": "scripts/evaluate_policy_gate.py",
                "phase_control.authoritative_sources.evaluator_function": "gateway.policy.gate_eval.evaluate_gate",
            },
        },
        "cp3_readiness_metrics_fail_cp3_02.json": {
            "metrics.false_positive_gate_failures": 1,
        },
        "cp3_readiness_metrics_fail_cp3_03.json": {
            "metrics.approved_overrides": 7,
        },
        "cp3_readiness_metrics_fail_cp3_04.json": {
            "metrics.policy_pass_or_valid_override_events": 71,
        },
        "cp3_readiness_metrics_fail_cp3_05.json": {
            "metrics.promotions_with_required_canary_soak_evidence": 17,
        },
        "cp3_readiness_metrics_fail_cp3_06.json": {
            "metrics.open_critical_policy_exceptions": 1,
        },
    }

    for filename, updates in fail_cases.items():
        _write_json(output_dir / filename, _apply_overrides(base, updates))

    print(f"CP3_FIXTURES_GENERATED {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
