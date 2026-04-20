import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _load_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _derive_policy_gate_outcome(log_text: str) -> str:
    if not log_text:
        return "NOT_PROVIDED"
    if "POLICY_GATE_FAIL" in log_text:
        return "FAIL"
    if "POLICY_GATE_PASS" in log_text:
        return "PASS"
    return "UNKNOWN"


def _derive_cp3_cli_outcome(log_text: str) -> str:
    if not log_text:
        return "NOT_PROVIDED"
    if "CP3_READINESS_FAIL" in log_text or "CP3_READINESS_ERROR" in log_text:
        return "FAIL"
    if "CP3_READINESS_PASS" in log_text:
        return "PASS"
    return "UNKNOWN"


def _render_markdown(
    cycle_id: str,
    date_str: str,
    phase: str,
    scope: str,
    report: dict[str, Any],
    policy_gate_outcome: str,
    cp3_cli_outcome: str,
) -> str:
    ready = bool(report.get("ready"))
    decision = "GO" if ready else "HOLD"
    target_phase = report.get("target_rollout_phase", "unknown")
    target_mode = report.get("target_mode", "unknown")
    criteria_results = report.get("criteria_results", [])
    if not isinstance(criteria_results, list):
        criteria_results = []

    lines = [
        "# CHIMERA V2 CP4 Policy Status",
        "",
        f"Cycle ID: `{cycle_id}`  ",
        f"Phase: `{phase}`  ",
        f"Date: `{date_str}`  ",
        f"Scope: `{scope}`",
        "",
        "## Summary",
        "",
        f"- CP3 readiness decision: `{'PASS' if ready else 'FAIL'}`",
        f"- Transition target: `{target_phase}` (`{target_mode}`)",
        f"- Policy gate command status: `{policy_gate_outcome}`",
        f"- CP3 readiness command status: `{cp3_cli_outcome}`",
        "",
        "## Criteria Results",
        "",
        "| Criterion ID | Name | Required | Result | Message |",
        "| --- | --- | --- | --- | --- |",
    ]

    for criterion in criteria_results:
        if not isinstance(criterion, dict):
            continue
        criterion_id = str(criterion.get("criterion_id", "unknown"))
        name = str(criterion.get("name", "unknown"))
        required = "true" if bool(criterion.get("required")) else "false"
        result = "PASS" if bool(criterion.get("passed")) else "FAIL"
        message = str(criterion.get("message", "")).replace("|", "/")
        lines.append(f"| {criterion_id} | {name} | {required} | {result} | {message} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Decision: `{decision}`",
            (
                "- Rationale: all required CP3 criteria passed."
                if ready
                else "- Rationale: one or more required CP3 criteria failed."
            ),
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a CP4 status markdown document from CP3 readiness report + command logs."
    )
    parser.add_argument("--cycle-id", required=True, help="Cycle identifier")
    parser.add_argument("--date", required=True, help="Status date in YYYY-MM-DD form")
    parser.add_argument("--phase", default="CP4 Policy Enforcement Status", help="Status phase label")
    parser.add_argument(
        "--scope",
        default="repo-local (MyFortress only)",
        help="Scope label rendered in the status doc",
    )
    parser.add_argument("--report", required=True, help="Path to CP3 readiness report JSON")
    parser.add_argument(
        "--policy-gate-log",
        default=None,
        help="Optional path to policy-gate command output log",
    )
    parser.add_argument(
        "--cp3-log",
        default=None,
        help="Optional path to CP3-readiness command output log",
    )
    parser.add_argument("--output", required=True, help="Path to generated markdown status document")
    args = parser.parse_args()

    report = _load_json(Path(args.report))
    policy_gate_text = _load_text(Path(args.policy_gate_log) if args.policy_gate_log else None)
    cp3_log_text = _load_text(Path(args.cp3_log) if args.cp3_log else None)

    rendered = _render_markdown(
        cycle_id=args.cycle_id,
        date_str=args.date,
        phase=args.phase,
        scope=args.scope,
        report=report,
        policy_gate_outcome=_derive_policy_gate_outcome(policy_gate_text),
        cp3_cli_outcome=_derive_cp3_cli_outcome(cp3_log_text),
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    print(f"CP4_STATUS_RENDERED {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
