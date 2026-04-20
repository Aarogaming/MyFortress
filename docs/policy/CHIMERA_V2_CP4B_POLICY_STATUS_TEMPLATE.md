# CHIMERA V2 CP4-B Policy Status (Template)

Cycle ID: `<cycle-id>`  
Phase: `CP4-B Policy Enforcement Status`  
Date: `<yyyy-mm-dd>`  
Scope: `repo-local (MyFortress only)`

## Enforcement State

- Active rollout phase: `<observe|soft_fail|hard_fail>`
- Active mode: `<advisory|required_with_override|required_fail_closed>`
- Hard-fail enabled: `<true|false>`
- Evaluator authority: `scripts/evaluate_policy_gate.py` -> `gateway.policy.gate_eval.evaluate_gate`
- Policy authority: `docs/policy/JANUS_GATE_POLICY_V1.json`

## CP3 Transition Matrix Check

| ID | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| CP3-01 | Authoritative policy/evaluator pinned | `<PASS|FAIL>` | `<evidence>` |
| CP3-02 | False-positive rate clean | `<PASS|FAIL>` | `<evidence>` |
| CP3-03 | Soft-fail override rate below threshold | `<PASS|FAIL>` | `<evidence>` |
| CP3-04 | Workflow policy compliance complete | `<PASS|FAIL>` | `<evidence>` |
| CP3-05 | Canary soak evidence complete | `<PASS|FAIL>` | `<evidence>` |
| CP3-06 | Open critical exceptions closed | `<PASS|FAIL>` | `<evidence>` |

## Verification Commands

```bash
python3 scripts/evaluate_policy_gate.py --envelope artifacts/policy/envelope_r1_composition_example.json
python3 scripts/evaluate_policy_gate.py --envelope artifacts/policy/envelope_r2_maelstrom_canary_example.json
make policy-gate
make policy-gate-negative
python3 scripts/evaluate_cp3_readiness.py --metrics artifacts/policy/cp3_readiness_metrics_example.json --output artifacts/policy/cp3_readiness_report_example.json --strict
python3 scripts/generate_policy_trend_snapshot.py --metrics artifacts/policy/cp3_readiness_metrics_example.json --report artifacts/policy/cp3_readiness_report_example.json --output artifacts/ci/policy_trend_<snapshot-id>.json
make cp4-status SNAPSHOT_ID=<snapshot-id> TREND_OUTPUT=artifacts/ci/policy_trend_<snapshot-id>.json
```

## Decision

- Decision: `<HOLD|GO>`
- Rationale: `<short rationale>`
- Next pass actions:
1. `<action one>`
2. `<action two>`
