#!/usr/bin/env python3
"""MyFortress local Merlin research-manager consumer helpers."""

from __future__ import annotations

import argparse
import json
import uuid
from typing import Any


OP_SESSION_CREATE = "merlin.research.manager.session.create"
OP_SESSIONS_LIST = "merlin.research.manager.sessions.list"
OP_SESSION_GET = "merlin.research.manager.session.get"
OP_SESSION_SIGNAL_ADD = "merlin.research.manager.session.signal.add"
OP_BRIEF_GET = "merlin.research.manager.brief.get"

REQUIRED_OPERATIONS = frozenset(
    {
        OP_SESSION_CREATE,
        OP_SESSION_GET,
        OP_BRIEF_GET,
    }
)

OPTIONAL_OPERATIONS = frozenset(
    {
        OP_SESSIONS_LIST,
        OP_SESSION_SIGNAL_ADD,
    }
)


def _collect_operation_names(node: Any, sink: set[str]) -> None:
    if isinstance(node, str):
        value = node.strip()
        if value.startswith("merlin."):
            sink.add(value)
        return
    if isinstance(node, dict):
        for key in ("name", "id", "operation", "capability"):
            value = node.get(key)
            if isinstance(value, str):
                candidate = value.strip()
                if candidate.startswith("merlin."):
                    sink.add(candidate)
        for value in node.values():
            _collect_operation_names(value, sink)
        return
    if isinstance(node, list):
        for value in node:
            _collect_operation_names(value, sink)


def extract_operation_names(capabilities_payload: Any) -> list[str]:
    names: set[str] = set()
    _collect_operation_names(capabilities_payload, names)
    return sorted(names)


def detect_research_manager_route(capabilities_payload: Any) -> dict[str, Any]:
    available = extract_operation_names(capabilities_payload)
    available_set = set(available)
    missing_required = sorted(REQUIRED_OPERATIONS - available_set)
    available_optional = sorted(OPTIONAL_OPERATIONS & available_set)

    enabled = len(missing_required) == 0
    return {
        "research_manager_enabled": enabled,
        "selected_path": "research_manager" if enabled else "legacy_non_research",
        "reason": (
            "research_manager_capabilities_available"
            if enabled
            else "research_manager_capabilities_missing"
        ),
        "available_operations": available,
        "available_optional_operations": available_optional,
        "missing_core_operations": missing_required,
    }


def _build_operation_envelope(
    *, operation: str, payload: dict[str, Any], request_id: str | None = None
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "target_service": "Merlin",
        "operation": operation,
        "request_id": request_id or f"myfortress-merlin-rm-{uuid.uuid4().hex[:12]}",
        "payload": payload,
    }


def build_session_create_envelope(
    *, objective: str, context_refs: list[str] | None = None, request_id: str | None = None
) -> dict[str, Any]:
    return _build_operation_envelope(
        operation=OP_SESSION_CREATE,
        payload={
            "objective": objective,
            "context_refs": context_refs or [],
        },
        request_id=request_id,
    )


def build_session_signal_add_envelope(
    *,
    session_id: str,
    signal_type: str,
    signal_payload: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    return _build_operation_envelope(
        operation=OP_SESSION_SIGNAL_ADD,
        payload={
            "session_id": session_id,
            "signal_type": signal_type,
            "signal_payload": signal_payload,
        },
        request_id=request_id,
    )


def build_brief_get_envelope(
    *, session_id: str, brief_format: str = "summary", request_id: str | None = None
) -> dict[str, Any]:
    return _build_operation_envelope(
        operation=OP_BRIEF_GET,
        payload={
            "session_id": session_id,
            "format": brief_format,
        },
        request_id=request_id,
    )


def _extract_error_code(error_payload: Any) -> str:
    if isinstance(error_payload, dict):
        code = error_payload.get("code")
        if isinstance(code, str) and code.strip():
            return code.strip().upper()
        error_obj = error_payload.get("error")
        if isinstance(error_obj, dict):
            nested = error_obj.get("code")
            if isinstance(nested, str) and nested.strip():
                return nested.strip().upper()
    return "UNKNOWN"


def map_research_manager_fallback(
    *, error_payload: Any, requested_operation: str
) -> dict[str, Any]:
    code = _extract_error_code(error_payload)
    result = {
        "error_code": code,
        "requested_operation": requested_operation,
    }
    if code == "RESEARCH_MANAGER_READ_ONLY":
        result.update(
            {
                "selected_path": "legacy_non_research_non_mutating",
                "fallback_mode": "read_only_guard_non_mutating_fallback",
                "mutating_allowed": False,
                "recommended_read_operation": OP_BRIEF_GET,
            }
        )
        return result
    if code == "SESSION_NOT_FOUND":
        result.update(
            {
                "selected_path": "legacy_non_research",
                "fallback_mode": "session_lookup_or_bootstrap_legacy",
                "mutating_allowed": False,
            }
        )
        return result
    if code == "VALIDATION_ERROR":
        result.update(
            {
                "selected_path": "legacy_non_research",
                "fallback_mode": "repair_input_and_retry_legacy",
                "mutating_allowed": False,
            }
        )
        return result
    result.update(
        {
            "selected_path": "legacy_non_research",
            "fallback_mode": "unknown_error_fallback",
            "mutating_allowed": False,
        }
    )
    return result


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate MyFortress Merlin research-manager capability/fallback flows."
    )
    parser.add_argument("--capabilities-json", default=None)
    parser.add_argument("--error-json", default=None)
    parser.add_argument(
        "--requested-operation",
        default=OP_SESSION_CREATE,
    )
    args = parser.parse_args()

    output: dict[str, Any] = {}
    if args.capabilities_json:
        output["capability_gate"] = detect_research_manager_route(
            _load_json(args.capabilities_json)
        )
    if args.error_json:
        output["fallback"] = map_research_manager_fallback(
            error_payload=_load_json(args.error_json),
            requested_operation=args.requested_operation,
        )
    if not output:
        parser.print_help()
        return 2
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
