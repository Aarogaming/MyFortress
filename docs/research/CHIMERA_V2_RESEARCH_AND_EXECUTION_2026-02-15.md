# CHIMERA V2 Research And Execution

Cycle ID: `CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15`
Mode: `ULTRA-FAST PASS`

## FUNCTION_STATEMENT

Define and enforce policy-as-code gates for MyFortress composition workflow and
Maelstrom runtime promotion with risk-class controls (R0-R3), provenance and
attestation requirements, incident freeze/override handling, and phased rollout.

## EVIDENCE_REFERENCES

- `docs/GATE_GOVERNANCE_POINTER.md` (existing baseline is pointer + `make check`)
- `docs/MASTER_ROADMAP_SYNC.md` (single-writer fail-closed promotion policy baseline)
- `protocols/AGENT_INTEROP_V1.md` (artifact and interop contract expectations)
- `docs/policy/JANUS_GATE_POLICY_V1.json` (new machine-readable policy gates)
- `gateway/policy/gate_eval.py` (new executable enforcement logic)
- `scripts/evaluate_policy_gate.py` (new CLI gate evaluator)
- `docs/policy/JANUS_GATE_ENFORCEMENT_ROLLOUT.md` (new rollout + integration plan)

## MISMATCHES

1. Existing local gate governance only points to `make check`; no explicit
   composition/promotion policy enforcement exists.
2. No repo-local pass/fail logic existed for risk classes R0-R3.
3. No incident freeze/override packet checks existed for runtime promotion.
4. No provenance/attestation minimums were encoded for promotion decisions.
5. `protocols/AGENT_INTEROP_V1.md` references schema/scripts that are not present
   in this repo snapshot, reducing local contract enforcement confidence.

## PROPOSALS_TOP_10

1. Adopt `Janus Gate` policy JSON as the local source of truth for R0-R3 rules.
2. Require envelope evaluation for both composition and Maelstrom promotion.
3. Enforce path confinement to `MyFortress/**` in all gate packets.
4. Gate promotion on risk-specific control checks and approval-role minimums.
5. Gate promotion on verified attestation sets by risk class.
6. Enforce sha256 digest format for artifact/SBOM/test evidence.
7. Fail closed during incident freeze unless override packet is valid.
8. Timebox overrides by risk class and require role-based override approvals.
9. Roll out in observe -> soft_fail -> hard_fail phases with measurable exit criteria.
10. Emit gate packets/evidence for AAS and Guild governance feedback loops.

## TOP_5_DEEP_DIVE

1. Risk-class admission controls:
   R0-R3 now encode explicit required controls, approval thresholds, and allowed
   target environments to stop ad hoc promotion decisions.
2. Provenance/attestation hard requirements:
   Required fields and verified attestation types are encoded per risk class,
   preventing promotions without build/SBOM/test evidence.
3. Freeze/override fail-closed behavior:
   Freeze mode blocks promotion by default; override requires ticket, reason,
   roles, and strict max time window by risk class.
4. Workflow-specific policy checks:
   Composition and Maelstrom promotion each require dedicated metadata and digest
   fields; Maelstrom transitions are constrained to allowed stage hops only.
5. Enforceable local command path:
   `scripts/evaluate_policy_gate.py` + `make policy-gate` provide deterministic
   local/CI evaluation using policy and envelope artifacts.

## COMPOSITION_ALIGNMENT

- Composition workflow now requires `workflow_metadata.composition_spec_digest`.
- R0/R1 are optimized for composition admission with lower blast radius controls.
- Scope confinement and compatibility/runbook evidence are mandatory before pass.

## MAELSTROM_ALIGNMENT

- Runtime promotion workflow requires `runtime_bundle_digest` and stage metadata.
- Allowed transitions are constrained (`dev->staging`, `staging->canary`,
  `canary->prod`).
- R2/R3 controls prioritize threat review, canary soak, rollback, and holdpoints.

## MYTHIC_ANCHOR_MAP

- mythic_name: `Janus Gate`
- collision_result:
  - query: `Janus Gate`
  - scope: `MyFortress/**`
  - collision_found: `false`
  - colliding_paths: `[]`
- fallback_plain_name: `composition-maelstrom-promotion-gate`

## THIN_SLICE_NEXT

1. Add CI job step that evaluates real promotion envelopes (not only examples).
2. Add signed attestation verification against trusted issuer identities.
3. Export gate outcomes into AAS/Guild dashboards for override-rate tracking.

## VERIFICATION_COMMANDS_RUN

- `python3 scripts/evaluate_policy_gate.py --envelope artifacts/policy/envelope_r1_composition_example.json` -> `PASS`
- `python3 scripts/evaluate_policy_gate.py --envelope artifacts/policy/envelope_r2_maelstrom_canary_example.json` -> `PASS`
- `make policy-gate` -> `PASS`
- `pytest -q tests/test_policy_gate.py` -> `5 passed`
- `python3 -m py_compile gateway/policy/gate_eval.py scripts/evaluate_policy_gate.py tests/test_policy_gate.py` -> `PASS`
- `python3 -m black --check gateway/policy tests/test_policy_gate.py scripts/evaluate_policy_gate.py` -> `FAILED` (`No module named black`)
- `python3 -m ruff check gateway/policy tests/test_policy_gate.py scripts/evaluate_policy_gate.py` -> `FAILED` (`No module named ruff`)

## ARTIFACTS_PRODUCED

- `docs/policy/JANUS_GATE_POLICY_V1.json`
- `docs/policy/JANUS_GATE_ENFORCEMENT_ROLLOUT.md`
- `gateway/policy/gate_eval.py`
- `gateway/policy/__init__.py`
- `scripts/evaluate_policy_gate.py`
- `artifacts/policy/envelope_r1_composition_example.json`
- `artifacts/policy/envelope_r2_maelstrom_canary_example.json`
- `tests/test_policy_gate.py`
