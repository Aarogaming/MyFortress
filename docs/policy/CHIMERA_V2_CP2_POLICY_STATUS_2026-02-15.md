# CHIMERA V2 CP2 Policy Status

Cycle ID: `CHIMERA-V2-RESEARCH-AND-EXECUTION-2026-02-15`  
Phase: `CP2 Advisory Enforcement`  
Date: `2026-02-15`

## CP2 State

- Policy authority: `docs/policy/JANUS_GATE_POLICY_V1.json`
- Evaluator authority: `scripts/evaluate_policy_gate.py` -> `gateway.policy.gate_eval.evaluate_gate`
- Active rollout phase: `observe`
- Active mode: `advisory`
- Hard-fail mode active: `false`

## CP3 Enforce-Transition Matrix

Decision rule: all criteria required (`all_criteria_required`) before changing rollout
phase to `hard_fail` (`required_fail_closed`).

| ID | Required truth before hard fail | Window | Threshold |
| --- | --- | --- | --- |
| CP3-01 | Authoritative policy and evaluator are pinned to Janus v1 paths | Decision timestamp | Exact path/function match |
| CP3-02 | Advisory runs show zero false-positive gate failures | 3 consecutive release runs | `false_positive_gate_failures / total_gate_evaluations <= 0.0` |
| CP3-03 | Soft-fail burn-in override rate is controlled | 2 consecutive release cycles | `approved_overrides / total_gate_evaluations <= 0.05` |
| CP3-04 | Promotions are policy-compliant (pass or valid override) | Most recent release cycle | `policy_pass_or_valid_override_events / total_promotion_attempts >= 1.0` |
| CP3-05 | Mandatory canary soak evidence is complete for gated transitions | Most recent release cycle | `promotions_with_required_canary_soak_evidence / staging_to_canary_and_canary_to_prod_promotions >= 1.0` |
| CP3-06 | No open critical policy exceptions remain | Decision timestamp | `open_critical_policy_exceptions <= 0` |

## Operational Notes

- CP2 remains advisory: evaluator output is authoritative evidence, but gate failures are
  not yet hard blockers.
- Transition to CP3 hard fail is explicitly blocked until all CP3 criteria pass.
