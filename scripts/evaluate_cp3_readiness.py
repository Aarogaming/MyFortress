import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from gateway.policy.cp3_readiness import evaluate_cp3_readiness_from_paths


DEFAULT_POLICY = Path("docs/policy/JANUS_GATE_POLICY_V1.json")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate CP3 hard-fail transition readiness from Janus policy + metrics."
    )
    parser.add_argument(
        "--policy",
        default=str(DEFAULT_POLICY),
        help="Path to policy JSON (default: docs/policy/JANUS_GATE_POLICY_V1.json)",
    )
    parser.add_argument(
        "--metrics",
        required=True,
        help="Path to CP3 readiness metrics JSON",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write machine-readable readiness report JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require observed authority values for exact-match criteria (for operator evidence hardening)",
    )
    args = parser.parse_args()

    try:
        report = evaluate_cp3_readiness_from_paths(
            policy_path=args.policy,
            metrics_path=args.metrics,
            require_observed_exact_match_fields=args.strict,
        )
    except Exception as exc:
        sys.stderr.write(f"CP3_READINESS_ERROR: {exc}\n")
        return 2

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if report["ready"]:
        print("CP3_READINESS_PASS")
        print(f"policy={args.policy}")
        print(f"metrics={args.metrics}")
        if args.output:
            print(f"report={args.output}")
        return 0

    sys.stderr.write("CP3_READINESS_FAIL\n")
    for failure in report["failures"]:
        sys.stderr.write(f"- {failure}\n")
    if args.output:
        sys.stderr.write(f"report={args.output}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
