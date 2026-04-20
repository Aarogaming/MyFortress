# Contract Validation in CI

Contract schemas live in `contracts/schema/`.

Validation in CI:
- `python scripts/validate_contracts.py --include-examples` is the authoritative validator.
- It validates `*.sample.json` and `*.example.json` fixtures under `contracts/examples/`
  (including control-plane EventEnvelope fixtures under `contracts/examples/control-plane/`).

Local validation entrypoints:
- Samples only: `python scripts/validate_contracts.py`
- Samples + examples: `python scripts/validate_contracts.py --include-examples`
- PowerShell wrapper: `eng/validate-contracts.ps1`

See `.github/workflows/ci.yml` and `docs/CONTRACT_TOOLING.md`.
