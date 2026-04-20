# CP3 Readiness Runbook

## Purpose

Provide a repeatable operator flow to decide if Janus Gate can transition from
advisory/soft-fail operation to hard-fail enforcement.

## Inputs

- Policy: `docs/policy/JANUS_GATE_POLICY_V1.json`
- CP3 metrics payload: `artifacts/policy/cp3_readiness_metrics_example.json` (or live equivalent)
- Optional latest CP3 report: `artifacts/policy/cp3_readiness_report_example.json`

## Required Metrics

The metrics payload must include:

- `false_positive_gate_failures`
- `total_gate_evaluations`
- `approved_overrides`
- `policy_pass_or_valid_override_events`
- `total_promotion_attempts`
- `promotions_with_required_canary_soak_evidence`
- `staging_to_canary_and_canary_to_prod_promotions`
- `open_critical_policy_exceptions`

## Procedure

1. Refresh metrics payload from current release-cycle telemetry.
   For repo fixture refresh, run:

```bash
make cp3-fixtures
```

2. Run CP3 readiness evaluation:

```bash
python3 scripts/evaluate_cp3_readiness.py \
  --metrics artifacts/policy/cp3_readiness_metrics_example.json \
  --output artifacts/policy/cp3_readiness_report_example.json \
  --strict
```

3. Confirm policy-gate baseline still passes:

```bash
make policy-gate
make policy-gate-negative
```

4. Review `artifacts/policy/cp3_readiness_report_example.json`:
- `ready=true` means all required CP3 criteria passed.
- `ready=false` means at least one required criterion failed.

## Decision Policy

- If `ready=false`: hold hard-fail transition and remediate failed criteria.
- If `ready=true` and governance sign-off is complete: proceed with controlled
  hard-fail enablement update in policy `pass_2.phase_control`.

## Artifacts To Preserve

- `artifacts/policy/cp3_readiness_report_example.json`
- `artifacts/ci/policy_gate_summary.txt` (CI artifact)
- `artifacts/ci/policy_trend_*.json` (trend snapshots)
- `artifacts/ci/policy_pipeline_summary.json` (command exit-code summary)

## Full Local Dry-Run

For a one-command local dry-run of the full pipeline (policy gate, negative gate,
CP3 readiness, trend snapshot, and CP4 status rendering), use:

```bash
SNAPSHOT_ID="local-$(date -u +%Y%m%dT%H%M%SZ)" && \
make cp4-status SNAPSHOT_ID="${SNAPSHOT_ID}" TREND_OUTPUT="artifacts/ci/policy_trend_${SNAPSHOT_ID}.json"
```
