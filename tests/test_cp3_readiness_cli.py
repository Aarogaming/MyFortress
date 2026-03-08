from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts/evaluate_cp3_readiness.py"
POLICY_PATH = REPO_ROOT / "docs/policy/JANUS_GATE_POLICY_V1.json"
ARTIFACTS_POLICY_DIR = REPO_ROOT / "artifacts/policy"


def _run_cli(
    metrics_path: Path, output_path: Path | None = None
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--policy",
        str(POLICY_PATH),
        "--metrics",
        str(metrics_path),
    ]
    if output_path is not None:
        cmd.extend(["--output", str(output_path)])

    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_cli_strict(
    metrics_path: Path, output_path: Path | None = None
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--policy",
        str(POLICY_PATH),
        "--metrics",
        str(metrics_path),
        "--strict",
    ]
    if output_path is not None:
        cmd.extend(["--output", str(output_path)])

    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cp3_readiness_cli_pass_exit_zero_and_writes_report(tmp_path: Path):
    output_path = tmp_path / "cp3_report.json"
    result = _run_cli(
        metrics_path=ARTIFACTS_POLICY_DIR / "cp3_readiness_metrics_example.json",
        output_path=output_path,
    )
    assert result.returncode == 0
    assert "CP3_READINESS_PASS" in result.stdout
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ready"] is True


def test_cp3_readiness_cli_strict_mode_passes_with_observed_values():
    result = _run_cli_strict(
        metrics_path=ARTIFACTS_POLICY_DIR / "cp3_readiness_metrics_example.json"
    )
    assert result.returncode == 0
    assert "CP3_READINESS_PASS" in result.stdout


def test_cp3_readiness_cli_fails_with_non_zero_exit_for_cp3_criterion_fixtures():
    checks = [
        ("cp3_readiness_metrics_fail_cp3_01.json", "CP3-01"),
        ("cp3_readiness_metrics_fail_cp3_02.json", "CP3-02"),
        ("cp3_readiness_metrics_fail_cp3_03.json", "CP3-03"),
        ("cp3_readiness_metrics_fail_cp3_04.json", "CP3-04"),
        ("cp3_readiness_metrics_fail_cp3_05.json", "CP3-05"),
        ("cp3_readiness_metrics_fail_cp3_06.json", "CP3-06"),
    ]

    for filename, criterion in checks:
        result = _run_cli(metrics_path=ARTIFACTS_POLICY_DIR / filename)
        assert result.returncode == 2
        assert "CP3_READINESS_FAIL" in result.stderr
        assert criterion in result.stderr


def test_cp3_readiness_cli_returns_error_for_schema_invalid_metrics(tmp_path: Path):
    invalid_metrics = tmp_path / "invalid_metrics.json"
    invalid_metrics.write_text(
        json.dumps(
            {
                "cycle_id": "CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15",
                "metrics": {"total_gate_evaluations": 10},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_cli(metrics_path=invalid_metrics)
    assert result.returncode == 2
    assert "CP3_READINESS_ERROR" in result.stderr


def test_cp3_readiness_cli_strict_mode_requires_observed_values(tmp_path: Path):
    strict_missing_observed = tmp_path / "strict_missing_observed.json"
    strict_missing_observed.write_text(
        json.dumps(
            {
                "cycle_id": "CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15",
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
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_cli_strict(metrics_path=strict_missing_observed)
    assert result.returncode == 2
    assert "CP3_READINESS_FAIL" in result.stderr
    assert "CP3-01" in result.stderr
    assert "missing in observed_values" in result.stderr
