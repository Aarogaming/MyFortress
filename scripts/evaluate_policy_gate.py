import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from gateway.policy import evaluate_from_paths, parse_utc


DEFAULT_POLICY = Path("docs/policy/JANUS_GATE_POLICY_V1.json")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a composition/promotion envelope against Janus Gate policy."
    )
    parser.add_argument(
        "--policy",
        default=str(DEFAULT_POLICY),
        help="Path to policy JSON (default: docs/policy/JANUS_GATE_POLICY_V1.json)",
    )
    parser.add_argument("--envelope", required=True, help="Path to envelope JSON to evaluate")
    parser.add_argument(
        "--now-utc",
        default=None,
        help="Optional evaluation timestamp in RFC3339 UTC form (for deterministic checks)",
    )
    args = parser.parse_args()

    now_utc = parse_utc(args.now_utc) if args.now_utc else None
    if args.now_utc and now_utc is None:
        sys.stderr.write(f"Invalid --now-utc value: {args.now_utc}\n")
        return 2

    errors = evaluate_from_paths(
        policy_path=args.policy,
        envelope_path=args.envelope,
        now_utc=now_utc,
    )
    if errors:
        sys.stderr.write("POLICY_GATE_FAIL\n")
        for error in errors:
            sys.stderr.write(f"- {error}\n")
        return 2

    print("POLICY_GATE_PASS")
    print(f"policy={args.policy}")
    print(f"envelope={args.envelope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
