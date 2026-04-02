# Implementation Plan: Public API Proxy

**Branch**: `001-public-api-proxy` | **Date**: 2026-03-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-public-api-proxy/spec.md`

## Summary

A simple Python/FastAPI web service that acts as a proxy over three free, no-key public APIs.
It exposes four endpoints: `GET /health`, `GET /ip` (caller IPv4 from request headers),
`GET /weather` (today's forecast via Open-Meteo), and `GET /rates` (currency exchange rates
via Frankfurter). No database, no caching, no authentication. Business logic lives in a
dedicated service layer; route handlers are thin. All endpoints return JSON; all errors return
`{"detail": "..."}` with appropriate HTTP status codes.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI ≥ 0.110.0, uvicorn[standard] ≥ 0.29.0, httpx ≥ 0.27.0, pydantic v2 (bundled with FastAPI)
**Storage**: N/A — no database, no persistent storage
**Testing**: pytest ≥ 8.0.0, pytest-cov ≥ 5.0.0
**Target Platform**: Linux server / local dev (any platform supporting Python 3.11+)
**Project Type**: web-service
**Performance Goals**: All data endpoints respond in under 3 seconds end-to-end (SC-004); `/health` responds under 1 second (SC-003)
**Constraints**: No auth, no DB, no caching, no API keys for upstream services (v1 scope)
**Scale/Scope**: Single developer, 3 data endpoints + health, simple proxy pattern

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Notes |
|-----------|------|--------|-------|
| I. API-First | All features exposed as HTTP endpoints with defined JSON contracts | ✅ PASS | 4 endpoints with full contracts in `contracts/api-contracts.md` |
| II. Simplicity & YAGNI | No DB, no caching, no auth; business logic in service layer | ✅ PASS | Services handle upstream calls; routers call services only |
| III. Test-First | Integration + unit tests required before implementation | ✅ PASS | Test structure defined; tests MUST be written before implementation code |
| IV. Explicit Error Handling | All errors return `{"detail": "..."}` + correct HTTP code; no stack trace leaks | ✅ PASS | HTTP 422 for validation, 502 for upstream failures, defined in contracts |
| V. Observability | `/health` endpoint + request logging + startup logging | ✅ PASS | `GET /health` in FR-009; uvicorn access log + startup log in `main.py` |

**Constitution Check result: ALL GATES PASS. No violations. Complexity Tracking table not required.**

*Post-Phase 1 re-check*: Design confirmed. No new abstractions introduced. No constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-public-api-proxy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api-contracts.md # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/
├── main.py              # App factory, lifespan, request logging middleware, startup logging
├── routers/
│   ├── health.py        # GET /health
│   ├── ip.py            # GET /ip
│   ├── weather.py       # GET /weather
│   └── rates.py         # GET /rates
├── services/
│   ├── ip_service.py    # Extract caller IP from request headers
│   ├── weather_service.py  # Call Open-Meteo geocoding + forecast APIs
│   └── rates_service.py    # Call Frankfurter currency rates API
└── models/
    └── responses.py     # Pydantic models: IpResponse, WeatherForecast, ExchangeRates, ErrorResponse

tests/
├── conftest.py          # Shared fixtures: TestClient, mock patches for httpx
├── integration/
│   ├── test_ip.py       # Happy path + upstream failure for /ip
│   ├── test_weather.py  # Happy path + 422 + 502 for /weather
│   └── test_rates.py    # Happy path + 422 (future/invalid date) + 502 for /rates
└── unit/
    ├── test_ip_service.py       # Header extraction logic
    ├── test_weather_service.py  # WMO code mapping, temperature conversion, upstream error handling
    └── test_rates_service.py    # Date validation, future date rejection, upstream error handling

requirements.txt         # Production + dev dependencies (single file for simplicity)
pyproject.toml           # Ruff configuration (lint + format)
```

**Structure Decision**: Single-project layout (Option 1). Backend-only service with no frontend.
`src/` is a Python package (`src/` layout) to prevent accidental imports from the project root.
All source code under `src/`; all tests under `tests/`. Aligns with Constitution Principle II (Simplicity).

## Upstream Service Integrations

### IP Address (`GET /ip`)

No upstream HTTP call. IP extracted from request in priority order:
1. `X-Forwarded-For` header (first IP in comma-separated list)
2. `X-Real-IP` header
3. `request.client.host` (direct TCP connection)

If all three are absent/empty → HTTP 502 `{"detail": "Could not determine caller IP address"}`.

### Weather Forecast (`GET /weather`)

Two sequential httpx calls:

**Step 1 — Geocoding**:
```
GET https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1
```
- Returns `{"results": [{"name": "...", "latitude": ..., "longitude": ..., ...}]}`
- If `results` is empty → HTTP 422 `{"detail": "Location not found: {location}"}`
- If request fails → HTTP 502

**Step 2 — Forecast**:
```
GET https://api.open-meteo.com/v1/forecast
    ?latitude={lat}&longitude={lon}
    &daily=weathercode,temperature_2m_max,temperature_2m_min
    &forecast_days=1
    &timezone=auto
```
- Returns `{"daily": {"time": ["YYYY-MM-DD"], "weathercode": [N], "temperature_2m_max": [F], ...}}`
- WMO `weathercode` mapped to human-readable string in `weather_service.py`
- `temperature_f` derived: `round(temp_c * 9 / 5 + 32, 1)`
- If request fails → HTTP 502

### Currency Rates (`GET /rates`)

Date routing logic in `rates_service.py`:
- `date` > today (UTC) → raise `InvalidDateError` → HTTP 422 before any upstream call
- `date` == today → `GET https://api.frankfurter.app/latest?from={base}`
- `date` < today → `GET https://api.frankfurter.app/{date}?from={base}`

Response shape: `{"amount": 1.0, "base": "USD", "date": "...", "rates": {...}}`
- `amount` and `base` from upstream are passed through; `rates` mapped directly.
- Upstream HTTP 404 (pre-1999 date) → HTTP 422 `{"detail": "No rates available for {date}"}`
- Any other upstream failure → HTTP 502

## Exception Handling Architecture

Custom exceptions defined in service modules, caught by FastAPI exception handlers registered in `main.py`:

```python
# src/main.py (outline)
app.add_exception_handler(UpstreamError, upstream_error_handler)     # → 502
app.add_exception_handler(LocationNotFoundError, validation_handler) # → 422
app.add_exception_handler(InvalidDateError, validation_handler)       # → 422
```

FastAPI's built-in `RequestValidationError` handler produces HTTP 422 with field-level detail automatically — no override needed.

## Logging

- **Request logging**: Uvicorn's built-in access log (`--log-level info`) covers method, path, status, response time.
- **Startup logging**: `lifespan` context in `main.py` logs Python version, FastAPI version, and bound address at startup.
- No additional logging framework required for v1.

## Complexity Tracking

> No violations recorded. Complexity Tracking table not applicable.
