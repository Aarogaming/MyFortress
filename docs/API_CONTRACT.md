# MyFortress HTTP API (draft)

Base URL defaults to `http://127.0.0.1:8100`. If `HOMEGATEWAY_API_KEY` is set, include header `x-api-key: <token>`.

## System
- `GET /system/info` → `{"platform": str, "python_version": str, "app_version": str, "start_time": float}`

## Health
- `GET /health` → `{"status": "ok"|"error", "home_assistant": "ok"|"error", "frigate": "ok"|"error"}`
- `GET /readiness` → `{"status": "ready"}`
- `GET /metrics` → `{"request_count": int, "uptime_seconds": float, "upstream": metrics_object}`

## Home Merlin
- `POST /home-assistant/probe`
  - Body: `{ base_url?, token?, verify_ssl?, entities: [id, ...] }`
  - Response: `{ healthy: bool, readings: { entity_id: { state, attributes, error? } }, error? }`
- `POST /home-assistant/service`
  - Body: `{ domain: str, service: str, data?: object, base_url?, token? }`
  - Response: `{ success: bool, response?: object, error?: str }`
- `POST /home-assistant/state`
  - Body: `{ entity_id: str, state: any, attributes?: object, base_url?, token? }`
  - Response: `{ success: bool, state?: any, attributes?: object, error?: str }`

## Frigate
- `POST /frigate/probe`
  - Body: `{ base_url?, api_key? }`
  - Response: `{ healthy: bool, version?: { version?, extra }, error?: str }`
- `GET /frigate/cameras`
  - Response: `{ success: bool, cameras: [name], error?, config?: object }`
- `GET /frigate/events?limit=50`
  - Response: `{ success: bool, events: [event], error? }`
- `GET /frigate/events/stream` (SSE)
  - Response: `text/event-stream`, yields lines `data: <raw>`; no buffering/keepalive implemented yet.
  - Basic reconnection with exponential backoff built in.

## Snapshot
- `POST /snapshot`
  - Body: `{ include_home_assistant?: bool, include_frigate?: bool, include_frigate_cameras?: bool, home_assistant_entities?: [id] }`
  - Response: `{ home_assistant?: <probe response>, frigate?: <probe response + cameras> }`
  - Cached per flag/entity-set with TTL `HOMEGATEWAY_SNAPSHOT_CACHE_TTL`.

## Python client (AAS/plugin)
- `gateway/clients/aas.py` and `plugins/home_gateway/client.py` expose async methods: `health()`, `snapshot()`, `probe_home_assistant()`, `home_assistant_service()`, `probe_frigate()`, `frigate_cameras()`.

## OpenAPI
- Generate `artifacts/openapi.json` via `make openapi` (uses `scripts/export_openapi.py`).

## gRPC
- Server runs on `PORT + 1` (default `8101`).
- See `artifacts/api/homegateway.proto` for parity RPCs (health, probes, HA service/state, Frigate probes/events, snapshot).
- Supports `x-api-key` metadata for authentication.

## Rate limiting
- Global simple sliding-window limit enforced per `x-client-id` (or source IP) in middleware: 120 requests/minute default. Exceeding returns HTTP 429. Include `x-client-id` header for consistent identity. Rate limiter is in-memory; not distributed.

## Metrics
- `GET /metrics` returns JSON including upstream latency/error counters.
- `GET /metrics/prom` exposes Prometheus text format (gauges for latencies, counters for upstream ops).
- Rate limit counters: `rate_limit_hits` and `rate_limit_hits_<path>` exported in `/metrics/prom`.

## Pending/Next
- Additional HA/Frigate operations (camera snapshots) to be added.
