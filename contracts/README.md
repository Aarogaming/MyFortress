# Contract Hygiene & Validation

All contracts must:
- Use JSON Schema in `contracts/schema/`
  - Payload contracts should use draft 2020-12.
  - Envelope/boundary contracts may use Draft 7 when runtime validation tooling requires it.
- Provide at least one example under `contracts/examples/` that validates against the schema
  - `*.example.json` is the canonical payload fixture naming.
  - `*.sample.json` is CI-required fixture naming.
- Be registered in `contracts/contracts.json`
- Prefer additive/backwards-compatible changes; breaking changes require a new schema version

## CI Requirements
- Contract fixtures are validated in CI using `python scripts/validate_contracts.py --include-examples`
- Validation failures must be fixed before merging

## Versioning
- Increment schema version for any change
- Deprecate old versions only after migration

## How to Add a Contract
1. Create schema in `contracts/schema/`
2. Add example(s) in `contracts/examples/`
3. Register in `contracts/contracts.json`
4. Run `python scripts/validate_contracts.py --include-examples` to verify

---
See main README for architecture and orchestration details.
