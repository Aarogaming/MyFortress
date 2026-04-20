from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from gateway.policy.cp3_readiness import evaluate_cp3_readiness
from gateway.policy.gate_eval import evaluate_from_paths, evaluate_gate, load_json

POLICY_PATH = Path(__file__).resolve().parent.parent / "docs/policy/JANUS_GATE_POLICY_V1.json"
ARTIFACTS_POLICY_DIR = Path(__file__).resolve().parent.parent / "artifacts/policy"
POLICY = load_json(POLICY_PATH)
NOW_UTC = datetime(2026, 2, 15, 12, 0, 0, tzinfo=timezone.utc)


def _digest(ch: str) -> str:
    return f"sha256:{ch * 64}"


def _base_cp3_metrics() -> dict[str, object]:
    return {
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


def _fails_for(result: dict[str, object], criterion_id: str) -> bool:
    failures = result.get("failures", [])
    if not isinstance(failures, list):
        return False
    return any(
        isinstance(failure, str) and failure.startswith(f"{criterion_id}:") for failure in failures
    )


def _base_r2_promotion_envelope() -> dict[str, object]:
    return {
        "cycle_id": "CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15",
        "workflow": "maelstrom_runtime_promotion",
        "risk_class": "R2",
        "target_environment": "canary",
        "scope_paths": [
            "MyFortress/gateway/core/service.py",
            "MyFortress/gateway/intelligence/manager.py",
        ],
        "controls": {
            "scope_confined_myfortress": True,
            "ticket_linked": True,
            "lint_test_type_passed": True,
            "threat_model_delta_reviewed": True,
            "runtime_guardrails_declared": True,
            "canary_soak_complete": True,
        },
        "approvals": [
            {"role": "service_owner"},
            {"role": "security_reviewer"},
        ],
        "provenance": {
            "source_repo": "MyFortress",
            "source_commit": "abcd1234",
            "build_pipeline": "github://AaroneousAutomationSuite/MyFortress/.github/workflows/ci.yml",
            "artifact_digest": _digest("1"),
            "sbom_digest": _digest("2"),
            "test_report_digest": _digest("3"),
        },
        "attestations": [
            {"type": "build_provenance", "verified": True},
            {"type": "sbom_attestation", "verified": True},
            {"type": "test_results_attestation", "verified": True},
        ],
        "incident": {
            "freeze_active": False,
            "override_requested": False,
        },
        "workflow_metadata": {
            "runtime_bundle_digest": _digest("a"),
            "promotion_from": "staging",
            "promotion_to": "canary",
        },
    }


def test_r2_maelstrom_promotion_passes_with_complete_envelope():
    envelope = _base_r2_promotion_envelope()
    errors = evaluate_gate(POLICY, envelope, now_utc=NOW_UTC)
    assert errors == []


def test_missing_required_control_fails():
    envelope = _base_r2_promotion_envelope()
    envelope["controls"]["canary_soak_complete"] = False
    errors = evaluate_gate(POLICY, envelope, now_utc=NOW_UTC)
    assert any("canary_soak_complete" in err for err in errors)


def test_incident_freeze_blocks_without_override():
    envelope = _base_r2_promotion_envelope()
    envelope["incident"] = {
        "freeze_active": True,
        "override_requested": False,
    }
    errors = evaluate_gate(POLICY, envelope, now_utc=NOW_UTC)
    assert any("freeze is active" in err for err in errors)


def test_r2_incident_override_requires_roles_and_window():
    envelope = _base_r2_promotion_envelope()
    envelope["incident"] = {
        "freeze_active": True,
        "override_requested": True,
        "override_ticket": "INC-2026-0215-001",
        "override_reason": "Critical recovery change after production control-plane incident.",
        "override_approval_roles": ["security_reviewer", "incident_commander"],
        "override_requested_at_utc": "2026-02-15T12:00:00Z",
        "override_expires_utc": "2026-02-15T12:45:00Z",
    }
    errors = evaluate_gate(POLICY, envelope, now_utc=NOW_UTC)
    assert errors == []


def test_scope_outside_myfortress_fails():
    envelope = _base_r2_promotion_envelope()
    envelope = deepcopy(envelope)
    envelope["scope_paths"] = ["OtherRepo/gateway/core/service.py"]
    errors = evaluate_gate(POLICY, envelope, now_utc=NOW_UTC)
    assert any("outside allowlist" in err for err in errors)


def test_negative_fixture_out_of_scope_fails():
    errors = evaluate_from_paths(
        policy_path=POLICY_PATH,
        envelope_path=ARTIFACTS_POLICY_DIR / "envelope_negative_out_of_scope.json",
        now_utc=NOW_UTC,
    )
    assert any("outside allowlist" in err for err in errors)


def test_negative_fixture_bad_transition_fails():
    errors = evaluate_from_paths(
        policy_path=POLICY_PATH,
        envelope_path=ARTIFACTS_POLICY_DIR / "envelope_negative_bad_transition.json",
        now_utc=NOW_UTC,
    )
    assert any("transition" in err and "not allowed" in err for err in errors)


def test_negative_fixture_missing_attestation_fails():
    errors = evaluate_from_paths(
        policy_path=POLICY_PATH,
        envelope_path=ARTIFACTS_POLICY_DIR / "envelope_negative_missing_attestation.json",
        now_utc=NOW_UTC,
    )
    assert any("sbom_attestation" in err for err in errors)


def test_negative_fixture_schema_invalid_fails():
    errors = evaluate_from_paths(
        policy_path=POLICY_PATH,
        envelope_path=ARTIFACTS_POLICY_DIR / "envelope_negative_schema_invalid.json",
        now_utc=NOW_UTC,
    )
    assert any("schema validation failed" in err for err in errors)


def test_cp3_readiness_reference_metrics_pass():
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=_base_cp3_metrics())
    assert result["ready"] is True
    assert result["failures"] == []

    criteria_results = result["criteria_results"]
    assert isinstance(criteria_results, list)
    criterion_ids = {row["criterion_id"] for row in criteria_results if isinstance(row, dict)}
    assert criterion_ids == {"CP3-01", "CP3-02", "CP3-03", "CP3-04", "CP3-05", "CP3-06"}


def test_cp3_01_authoritative_mapping_fails_on_policy_mismatch():
    policy = deepcopy(POLICY)
    policy["pass_2"]["phase_control"]["authoritative_sources"][
        "policy_path"
    ] = "docs/policy/NOT_JANUS_POLICY.json"

    result = evaluate_cp3_readiness(policy=policy, metrics_payload=_base_cp3_metrics())
    assert result["ready"] is False
    assert _fails_for(result, "CP3-01")


def test_cp3_02_false_positive_ratio_threshold_edge():
    metrics = _base_cp3_metrics()
    metrics["metrics"]["false_positive_gate_failures"] = 0
    metrics["metrics"]["total_gate_evaluations"] = 10
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-02") is False

    metrics["metrics"]["false_positive_gate_failures"] = 1
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-02")


def test_cp3_03_override_rate_threshold_edge():
    metrics = _base_cp3_metrics()
    metrics["metrics"]["approved_overrides"] = 5
    metrics["metrics"]["total_gate_evaluations"] = 100
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-03") is False

    metrics["metrics"]["approved_overrides"] = 6
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-03")


def test_cp3_04_policy_compliance_threshold_edge():
    metrics = _base_cp3_metrics()
    metrics["metrics"]["policy_pass_or_valid_override_events"] = 24
    metrics["metrics"]["total_promotion_attempts"] = 24
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-04") is False

    metrics["metrics"]["policy_pass_or_valid_override_events"] = 23
    metrics["metrics"]["total_promotion_attempts"] = 24
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-04")


def test_cp3_05_canary_coverage_threshold_edge():
    metrics = _base_cp3_metrics()
    metrics["metrics"]["promotions_with_required_canary_soak_evidence"] = 9
    metrics["metrics"]["staging_to_canary_and_canary_to_prod_promotions"] = 9
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-05") is False

    metrics["metrics"]["promotions_with_required_canary_soak_evidence"] = 8
    metrics["metrics"]["staging_to_canary_and_canary_to_prod_promotions"] = 9
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-05")


def test_cp3_06_open_exception_threshold_edge():
    metrics = _base_cp3_metrics()
    metrics["metrics"]["open_critical_policy_exceptions"] = 0
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-06") is False

    metrics["metrics"]["open_critical_policy_exceptions"] = 1
    result = evaluate_cp3_readiness(policy=POLICY, metrics_payload=metrics)
    assert _fails_for(result, "CP3-06")


def test_envelope_schema_validation_fails_on_missing_required_fields(tmp_path):
    invalid_envelope_path = tmp_path / "invalid_envelope.json"
    invalid_envelope_path.write_text(
        json.dumps(
            {
                "cycle_id": "CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15",
                "workflow": "composition",
                "risk_class": "R1",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    errors = evaluate_from_paths(
        policy_path=POLICY_PATH,
        envelope_path=invalid_envelope_path,
        now_utc=NOW_UTC,
    )
    assert any("schema validation failed" in err for err in errors)
