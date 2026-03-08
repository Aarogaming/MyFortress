from __future__ import annotations

from scripts.merlin_research_manager_consumer import (
    OP_BRIEF_GET,
    OP_SESSION_CREATE,
    OP_SESSION_SIGNAL_ADD,
    build_brief_get_envelope,
    build_session_create_envelope,
    build_session_signal_add_envelope,
    detect_research_manager_route,
    map_research_manager_fallback,
)


def test_capability_present_selects_research_manager_flow() -> None:
    payload = {
        "operations": [
            {"name": "merlin.research.manager.session.create"},
            {"name": "merlin.research.manager.session.get"},
            {"name": "merlin.research.manager.brief.get"},
            {"name": "merlin.research.manager.session.signal.add"},
        ]
    }
    decision = detect_research_manager_route(payload)
    assert decision["research_manager_enabled"] is True
    assert decision["selected_path"] == "research_manager"
    assert decision["missing_core_operations"] == []


def test_envelope_builders_emit_create_signal_brief_operations() -> None:
    create_env = build_session_create_envelope(objective="sync")
    signal_env = build_session_signal_add_envelope(
        session_id="sess-001",
        signal_type="observation",
        signal_payload={"source": "myfortress"},
    )
    brief_env = build_brief_get_envelope(session_id="sess-001")

    assert create_env["operation"] == OP_SESSION_CREATE
    assert signal_env["operation"] == OP_SESSION_SIGNAL_ADD
    assert brief_env["operation"] == OP_BRIEF_GET


def test_read_only_error_selects_non_mutating_fallback() -> None:
    decision = map_research_manager_fallback(
        error_payload={"error": {"code": "RESEARCH_MANAGER_READ_ONLY"}},
        requested_operation=OP_SESSION_CREATE,
    )
    assert decision["error_code"] == "RESEARCH_MANAGER_READ_ONLY"
    assert decision["selected_path"] == "legacy_non_research_non_mutating"
    assert decision["mutating_allowed"] is False
    assert decision["recommended_read_operation"] == OP_BRIEF_GET


def test_validation_error_maps_to_expected_fallback() -> None:
    decision = map_research_manager_fallback(
        error_payload={"error": {"code": "VALIDATION_ERROR"}},
        requested_operation="merlin.research.manager.session.get",
    )
    assert decision["error_code"] == "VALIDATION_ERROR"
    assert decision["selected_path"] == "legacy_non_research"
    assert decision["fallback_mode"] == "repair_input_and_retry_legacy"
