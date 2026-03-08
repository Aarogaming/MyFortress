# Janus Gate Enforcement Rollout

Cycle: `CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15`
Policy: `docs/policy/JANUS_GATE_POLICY_V1.json`

## Purpose

Roll out enforceable composition and Maelstrom promotion gates in three phases:
observe, soft fail, and hard fail.

## Rollout Phases

1. `observe` (advisory)
   - Evaluate envelopes and log violations.
   - No release blocking.
2. `soft_fail` (required with override)
   - Gate is required for all composition and promotion attempts.
   - Incident override path is available per risk class.
3. `hard_fail` (required fail-closed)
   - Gate failures block promotion attempts.
   - Freeze mode is fail-closed; only valid override packets can proceed.

## CP2 Authority Baseline

- Active cycle phase: `CP2 Advisory Enforcement`
- Active rollout phase: `observe`
- Active mode: `advisory`
- Hard fail enabled: `false`
- Authoritative policy: `docs/policy/JANUS_GATE_POLICY_V1.json`
- Authoritative evaluator entrypoint: `scripts/evaluate_policy_gate.py`
- Authoritative evaluator function: `gateway.policy.gate_eval.evaluate_gate`

## CP3 Hard-Fail Transition Matrix

All criteria below must pass before switching to `hard_fail`.

| ID | Criterion | Window | Threshold |
| --- | --- | --- | --- |
| CP3-01 | Authoritative policy/evaluator pinned | Decision timestamp | Exact match to Janus policy/evaluator paths |
| CP3-02 | False-positive gate failures | 3 consecutive release runs | `false_positive_gate_failures / total_gate_evaluations <= 0.0` |
| CP3-03 | Override rate during soft-fail burn-in | 2 consecutive release cycles | `approved_overrides / total_gate_evaluations <= 0.05` |
| CP3-04 | Workflow policy compliance | Most recent release cycle | `policy_pass_or_valid_override_events / total_promotion_attempts >= 1.0` |
| CP3-05 | Canary soak evidence coverage | Most recent release cycle | `promotions_with_required_canary_soak_evidence / staging_to_canary_and_canary_to_prod_promotions >= 1.0` |
| CP3-06 | Open critical policy exceptions | Decision timestamp | `open_critical_policy_exceptions <= 0` |

## Integration Points

### AAS integration

- Emit policy envelope + attestation bundle to AAS artifact bus before promotion.
- Attach MyFortress gate decision to AAS compatibility matrix evidence.
- Use `scripts/evaluate_policy_gate.py` as pre-promotion verifier in AAS automation.

### Guild integration

- Route R2/R3 override approvals through Guild governance quorum.
- Publish override/failure telemetry to Guild lane planning for policy tuning.
- Treat repeated override usage as governance debt in Guild review cadence.

### Maelstrom integration

- Apply gate evaluation immediately before `staging->canary` and `canary->prod`.
- Require `runtime_bundle_digest` and canary soak evidence for runtime promotion.
- Block transitions not listed in policy `allowed_transitions`.

## Local Verification Commands

```bash
python3 scripts/evaluate_policy_gate.py --envelope artifacts/policy/envelope_r1_composition_example.json
python3 scripts/evaluate_policy_gate.py --envelope artifacts/policy/envelope_r2_maelstrom_canary_example.json
```
