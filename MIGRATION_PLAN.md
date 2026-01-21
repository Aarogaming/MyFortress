# MyFortress Migration Plan

Goal: Separate MyFortress into a standalone service while keeping AAS functional via a thin plugin shim.

## Phases
1) **Layout/Config** *(done)*: core/api/integrations/clients established; config via `.env` with HA/Frigate settings and optional API key; request logging/middleware in place.
2) **Service Extraction** *(done)*: port plugin logic from `AAS/plugins/home_gateway` into async integrations; expand endpoints beyond probes (snapshots/actions/commands). *(Added HA service invocation + Frigate cameras; snapshot includes cameras; parallelized snapshot; gRPC server baseline.)*
3) **AAS Rewire** *(in progress)*: update `plugins/home_gateway` in AAS to call the standalone API (ship Python client) instead of local imports; keep fallback until validated. *(Feature-flagged service client added; fallback connectors remain; Python client module created.)*
4) **CI/Health** *(done)*: CI workflow, Dockerfile/compose, metrics/readiness; add package/build artifacts and release.

## TODOs (tracked in `artifacts/guild/ACTIVE_TASKS.md`)
- HG-001: Define standalone service layout and config *(scaffolded: config/env, middleware, CLI, HTTP client)*
- HG-002: Extract plugin logic into service, expose API *(probes/snapshot + HA service + Frigate cameras/events added; continue porting actions/state writes)*
- HG-003: Update AAS plugin to consume standalone API *(service client wired with env flag; validate + rollout)*
- HG-004: Add CI/build scripts and health checks *(CI/Docker/metrics in place; iterate on coverage + packaging)*
- HG-005: Implement Home Merlin + Frigate API endpoints *(probes + HA service + HA set_state + Frigate cameras/events; add more ops/telemetry)*
- HG-006: Publish client contract (HTTP/gRPC) + Python client for AAS *(HTTP client added; HTTP contract doc + OpenAPI export script added; proto draft at `artifacts/api/homegateway.proto`)*
- HG-007: Add integration tests for connectors/API *(baseline tests added; expand fixtures + error cases)*

## Notes
- Keep the AAS plugin intact until HG-002/HG-003 are completed; plan staged rollout with feature flag.
- Coordinate with GUI/Tray for status surfacing; with Home (assets/specs) for device data references.
