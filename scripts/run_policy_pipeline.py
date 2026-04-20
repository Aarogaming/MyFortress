import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the local policy pipeline and write a single summary artifact with command exit codes."
    )
    parser.add_argument("--cycle-id", required=True, help="Cycle identifier")
    parser.add_argument("--date", required=True, help="Status date in YYYY-MM-DD form")
    parser.add_argument("--snapshot-id", required=True, help="Snapshot identifier used for trend artifact")
    parser.add_argument(
        "--phase",
        default="CP4-B Policy Enforcement Status",
        help="Phase label for rendered CP4 status",
    )
    parser.add_argument(
        "--metrics",
        default="artifacts/policy/cp3_readiness_metrics_example.json",
        help="Path to CP3 metrics input JSON",
    )
    parser.add_argument(
        "--cp3-report",
        default="artifacts/policy/cp3_readiness_report_example.json",
        help="Path to CP3 readiness report output JSON",
    )
    parser.add_argument(
        "--policy-gate-log",
        default="artifacts/ci/policy_gate_summary.txt",
        help="Path to policy-gate log output",
    )
    parser.add_argument(
        "--policy-gate-negative-log",
        default="artifacts/ci/policy_gate_negative_summary.txt",
        help="Path to policy-gate-negative log output",
    )
    parser.add_argument(
        "--cp3-log",
        default="artifacts/ci/cp3_readiness_summary.txt",
        help="Path to CP3-readiness log output",
    )
    parser.add_argument(
        "--trend-output",
        required=True,
        help="Path to trend snapshot output JSON",
    )
    parser.add_argument(
        "--trend-log",
        default="artifacts/ci/policy_trend_generation_summary.txt",
        help="Path to trend generation log output",
    )
    parser.add_argument(
        "--status-output",
        required=True,
        help="Path to rendered CP4 status markdown",
    )
    parser.add_argument(
        "--status-log",
        default="artifacts/ci/cp4_status_render_summary.txt",
        help="Path to CP4 status render log output",
    )
    parser.add_argument(
        "--summary-output",
        default="artifacts/ci/policy_pipeline_summary.json",
        help="Path to pipeline summary JSON output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Run CP3 readiness with strict observed-value requirement",
    )
    args = parser.parse_args()

    python_cmd = sys.executable
    policy_gate_log = Path(args.policy_gate_log)
    policy_gate_negative_log = Path(args.policy_gate_negative_log)
    cp3_log = Path(args.cp3_log)
    trend_log = Path(args.trend_log)
    status_log = Path(args.status_log)

    cp3_command = [
        python_cmd,
        "scripts/evaluate_cp3_readiness.py",
        "--metrics",
        args.metrics,
        "--output",
        args.cp3_report,
    ]
    if args.strict:
        cp3_command.append("--strict")

    command_specs: list[dict[str, Any]] = [
        {
            "name": "policy_gate",
            "command": [python_cmd, "scripts/evaluate_policy_gate.py", "--envelope", "artifacts/policy/envelope_r1_composition_example.json"],
            "log_path": str(policy_gate_log),
        },
        {
            "name": "policy_gate_canary",
            "command": [python_cmd, "scripts/evaluate_policy_gate.py", "--envelope", "artifacts/policy/envelope_r2_maelstrom_canary_example.json"],
            "log_path": str(policy_gate_log),
            "append_log": True,
        },
        {
            "name": "policy_gate_negative",
            "command": [python_cmd, "scripts/check_policy_gate_negative.py"],
            "log_path": str(policy_gate_negative_log),
        },
        {
            "name": "cp3_readiness",
            "command": cp3_command,
            "log_path": str(cp3_log),
        },
        {
            "name": "trend_snapshot",
            "command": [
                python_cmd,
                "scripts/generate_policy_trend_snapshot.py",
                "--metrics",
                args.metrics,
                "--report",
                args.cp3_report,
                "--snapshot-id",
                args.snapshot_id,
                "--output",
                args.trend_output,
            ],
            "log_path": str(trend_log),
        },
        {
            "name": "cp4_status_render",
            "command": [
                python_cmd,
                "scripts/render_cp4_status.py",
                "--cycle-id",
                args.cycle_id,
                "--date",
                args.date,
                "--phase",
                args.phase,
                "--report",
                args.cp3_report,
                "--policy-gate-log",
                args.policy_gate_log,
                "--cp3-log",
                args.cp3_log,
                "--output",
                args.status_output,
            ],
            "log_path": str(status_log),
        },
    ]

    summary_commands: list[dict[str, Any]] = []
    overall_exit_code = 0

    for spec in command_specs:
        command = spec["command"]
        log_path = Path(spec["log_path"])
        append_log = bool(spec.get("append_log", False))

        result = subprocess.run(
            command,
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        log_text = result.stdout + result.stderr
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if append_log and log_path.exists():
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(log_text)
        else:
            log_path.write_text(log_text, encoding="utf-8")

        exit_code = int(result.returncode)
        if exit_code != 0:
            overall_exit_code = 2

        summary_commands.append(
            {
                "name": spec["name"],
                "command": shlex.join(command),
                "exit_code": exit_code,
                "log_path": str(log_path),
            }
        )

    generated_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    summary = {
        "schema_version": "policy_pipeline_summary_v1",
        "generated_utc": generated_utc,
        "cycle_id": args.cycle_id,
        "date": args.date,
        "snapshot_id": args.snapshot_id,
        "strict_mode": bool(args.strict),
        "commands": summary_commands,
        "overall_exit_code": overall_exit_code,
    }

    summary_path = Path(args.summary_output)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"POLICY_PIPELINE_SUMMARY_WRITTEN {summary_path}")
    return overall_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
