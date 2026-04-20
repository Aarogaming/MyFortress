# Control-plane envelope examples

This folder contains EventEnvelope wrappers for control-plane payload contracts
(Mesh/Swarm/Memory/Ops/Research/Builder/QA/UX).

Notes:
- These validate against `contracts/schema/event-envelope.v1.schema.json`.
- The nested payload contract is not fully validated by the EventEnvelope schema
  (by design). Validate payload contracts directly with their own schemas.
