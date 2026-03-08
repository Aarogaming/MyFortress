from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts/render_cp4_status.py"


def _run_render(
    report_path: Path,
    output_path: Path,
    policy_gate_log: Path | None = None,
    cp3_log: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--cycle-id",
        "CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15",
        "--date",
        "2026-02-15",
        "--phase",
        "CP4-B Policy Enforcement Status",
        "--report",
        str(report_path),
        "--output",
        str(output_path),
    ]
    if policy_gate_log is not None:
        cmd.extend(["--policy-gate-log", str(policy_gate_log)])
    if cp3_log is not None:
        cmd.extend(["--cp3-log", str(cp3_log)])

    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_render_cp4_status_pass_contract(tmp_path: Path):
    report = {
        "ready": True,
        "target_rollout_phase": "hard_fail",
        "target_mode": "required_fail_closed",
        "criteria_results": [
            {
                "criterion_id": "CP3-01",
                "name": "authoritative_policy_and_evaluator_pinned",
                "required": True,
                "passed": True,
                "message": "all expected values matched",
            }
        ],
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report) + "\n", encoding="utf-8")

    policy_gate_log = tmp_path / "policy_gate.log"
    policy_gate_log.write_text("POLICY_GATE_PASS\n", encoding="utf-8")
    cp3_log = tmp_path / "cp3.log"
    cp3_log.write_text("CP3_READINESS_PASS\n", encoding="utf-8")
    output_path = tmp_path / "cp4_status.md"

    result = _run_render(
        report_path=report_path,
        output_path=output_path,
        policy_gate_log=policy_gate_log,
        cp3_log=cp3_log,
    )
    assert result.returncode == 0
    assert output_path.exists()

    rendered = output_path.read_text(encoding="utf-8")
    assert "CP3 readiness decision: `PASS`" in rendered
    assert "Policy gate command status: `PASS`" in rendered
    assert "CP3 readiness command status: `PASS`" in rendered
    assert "| CP3-01 | authoritative_policy_and_evaluator_pinned | true | PASS |" in rendered
    assert "Decision: `GO`" in rendered


def test_render_cp4_status_fail_contract(tmp_path: Path):
    report = {
        "ready": False,
        "target_rollout_phase": "hard_fail",
        "target_mode": "required_fail_closed",
        "criteria_results": [
            {
                "criterion_id": "CP3-02",
                "name": "advisory_false_positive_rate_clean",
                "required": True,
                "passed": False,
                "message": "0.010000 > 0.000000",
            }
        ],
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report) + "\n", encoding="utf-8")

    policy_gate_log = tmp_path / "policy_gate.log"
    policy_gate_log.write_text("POLICY_GATE_FAIL\n", encoding="utf-8")
    cp3_log = tmp_path / "cp3.log"
    cp3_log.write_text("CP3_READINESS_FAIL\n- CP3-02\n", encoding="utf-8")
    output_path = tmp_path / "cp4_status.md"

    result = _run_render(
        report_path=report_path,
        output_path=output_path,
        policy_gate_log=policy_gate_log,
        cp3_log=cp3_log,
    )
    assert result.returncode == 0

    rendered = output_path.read_text(encoding="utf-8")
    assert "CP3 readiness decision: `FAIL`" in rendered
    assert "Policy gate command status: `FAIL`" in rendered
    assert "CP3 readiness command status: `FAIL`" in rendered
    assert "| CP3-02 | advisory_false_positive_rate_clean | true | FAIL |" in rendered
    assert "Decision: `HOLD`" in rendered
