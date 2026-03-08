from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts/generate_policy_trend_snapshot.py"
ARTIFACTS_POLICY_DIR = REPO_ROOT / "artifacts/policy"


def _run_snapshot(
    metrics_path: Path,
    output_path: Path,
    report_path: Path | None = None,
    snapshot_id: str = "local-contract",
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--metrics",
        str(metrics_path),
        "--snapshot-id",
        snapshot_id,
        "--output",
        str(output_path),
    ]
    if report_path is not None:
        cmd.extend(["--report", str(report_path)])

    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_policy_trend_snapshot_contract_with_report(tmp_path: Path):
    output_path = tmp_path / "trend.json"
    result = _run_snapshot(
        metrics_path=ARTIFACTS_POLICY_DIR / "cp3_readiness_metrics_example.json",
        report_path=ARTIFACTS_POLICY_DIR / "cp3_readiness_report_example.json",
        output_path=output_path,
        snapshot_id="contract-001",
    )
    assert result.returncode == 0
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "policy_trend_snapshot_v1"
    assert payload["snapshot_id"] == "contract-001"
    assert payload["trend_metrics"]["false_positive_rate"] == 0.0
    assert abs(payload["trend_metrics"]["override_rate"] - (4.0 / 120.0)) < 1e-12
    assert payload["cp3_readiness"]["ready"] is True
    assert payload["cp3_readiness"]["failure_count"] == 0


def test_policy_trend_snapshot_contract_without_report(tmp_path: Path):
    output_path = tmp_path / "trend_without_report.json"
    result = _run_snapshot(
        metrics_path=ARTIFACTS_POLICY_DIR / "cp3_readiness_metrics_example.json",
        output_path=output_path,
        snapshot_id="contract-002",
    )
    assert result.returncode == 0

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "policy_trend_snapshot_v1"
    assert payload["snapshot_id"] == "contract-002"
    assert payload["cp3_readiness"]["ready"] is None
    assert payload["cp3_readiness"]["failure_count"] == 0
