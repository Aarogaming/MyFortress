# CHIMERA V2 CP6 Parallel Consumer Merlin Research Manager Adoption Status

FUNCTION_STATEMENT
- Implemented repo-local MyFortress Merlin research-manager consumer helpers with tolerant capability gate, create->signal->brief envelope builders, and deterministic fallback mapping for expected error branches.

EVIDENCE_REFERENCES
- `scripts/merlin_research_manager_consumer.py`
- `tests/test_merlin_research_manager_consumer.py`
- `docs/research/CHIMERA_V2_CP6_PARALLEL_CONSUMER_MERLIN_RESEARCH_MANAGER_ADOPTION_STATUS_2026-02-17.md`

CHANGES_APPLIED
1. Added `scripts/merlin_research_manager_consumer.py` with capability extraction/gating, envelope builders, and fallback mapping.
2. Added `tests/test_merlin_research_manager_consumer.py` covering capability present flow, success envelope operation sequence, and expected failure branches.
3. Added this required CP6 adoption status artifact for intake/adjudication.

VERIFICATION_COMMANDS_RUN
1. `python3 -m pytest -q tests/test_merlin_research_manager_consumer.py`
   - Outcome: PASS
   - Result: `4 passed in 0.04s`
2. `python3 -m pytest -q tests/test_merlin_research_manager_consumer.py -k test_envelope_builders_emit_create_signal_brief_operations`
   - Outcome: PASS
   - Result: `1 passed, 3 deselected`
3. `python3 -m pytest -q tests/test_merlin_research_manager_consumer.py -k "test_read_only_error_selects_non_mutating_fallback or test_validation_error_maps_to_expected_fallback"`
   - Outcome: PASS
   - Result: `2 passed, 2 deselected`
4. `python -c "from pathlib import Path; print(Path('MyFortress/docs/research/CHIMERA_V2_CP6_PARALLEL_CONSUMER_MERLIN_RESEARCH_MANAGER_ADOPTION_STATUS_2026-02-17.md').exists())"`
   - Outcome: PASS
   - Result: `True`

ARTIFACTS_PRODUCED
- `MyFortress/docs/research/CHIMERA_V2_CP6_PARALLEL_CONSUMER_MERLIN_RESEARCH_MANAGER_ADOPTION_STATUS_2026-02-17.md`
- `MyFortress/scripts/merlin_research_manager_consumer.py`
- `MyFortress/tests/test_merlin_research_manager_consumer.py`

RISKS_AND_NEXT_PASS
1. No active CP6 intake blocker remains; deterministic envelope/fallback semantics and live-payload capability gating are both passing.
2. Next pass should add one direct live endpoint probe in the target runner window to complement fixture-based verification.

## FOLLOW_UP_2026_02_28_VERIFICATION
1. `python3 -m pytest -q tests/test_merlin_research_manager_consumer.py`
   - Outcome: PASS (`4 passed`)
2. `python3 scripts/merlin_research_manager_consumer.py --capabilities-json ../artifacts/diagnostics/merlin_operations_capabilities_probe_2026-02-28.json`
   - Outcome: PASS (`research_manager_enabled=true`, `selected_path=research_manager`)
3. Live capabilities fixture evidence used:
   - `artifacts/diagnostics/merlin_operations_capabilities_probe_2026-02-28.json`
   - required operations present: `session.create`, `session.get`, `brief.get`.

## FOLLOW_UP_2026_03_01_VERIFICATION
1. Bounded MyFortress consumer tests rerun:
   - `timeout 180s python3 -m pytest -q tests/test_merlin_research_manager_consumer.py`
   - Outcome: PASS (`4 passed`).
2. Direct live endpoint probe in a bounded local Merlin window:
   - Start temporary local Merlin (`127.0.0.1:8001`) with bounded startup wait.
   - Probe exact endpoint:
     `curl -sS -H "X-Merlin-Key: merlin-secret-key" http://127.0.0.1:8001/merlin/operations/capabilities`
   - Persisted artifact:
     `MyFortress/artifacts/diagnostics/merlin_operations_capabilities_probe_2026-03-01.json`
3. Consumer gate verification against refreshed live payload:
   - `timeout 120s python3 scripts/merlin_research_manager_consumer.py --capabilities-json artifacts/diagnostics/merlin_operations_capabilities_probe_2026-03-01.json`
   - Outcome: PASS (`research_manager_enabled=true`, `selected_path=research_manager`, `missing_core_operations=[]`).
4. Payload parity check vs prior probe baseline:
   - Compared refreshed artifact with `artifacts/diagnostics/merlin_operations_capabilities_probe_2026-02-28.json`.
   - Result: `capability_count=66` vs `66`, `required_missing_new=[]`, `added_vs_old=0`, `removed_vs_old=0`.
