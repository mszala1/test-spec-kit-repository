# Research: Public API Proxy

**Branch**: `001-public-api-proxy` | **Phase**: 0 | **Date**: 2026-03-25

## Decision 1: IP Address Resolution Strategy

**Decision**: Determine caller IP from incoming HTTP request headers — no upstream API call needed.

**Rationale**: An upstream "what is my IP" service would return the _proxy server's_ IP, not the _caller's_ IP. The correct approach for a proxy is to extract the IP from the request itself:
1. Check `X-Forwarded-For` header first (populated by reverse proxies and load balancers).
2. Fall back to `X-Real-IP` header.
3. Fall back to `request.client.host` (direct TCP connection address).

FastAPI's `Request` object exposes all of these natively. This approach is simpler, faster (no network hop), and more accurate.

**Alternatives considered**:
- Forward to `https://api.ipify.org` — Rejected: returns server IP, not caller IP.
- Forward to `https://ip-api.com` — Rejected: same problem; also has rate limits.

---

## Decision 2: Upstream Weather Service

**Decision**: Use **Open-Meteo** (https://open-meteo.com) — free, no API key, REST JSON, supports geocoding.

**Rationale**:
- Fully free with no registration or API key required (satisfies spec assumption).
- Two-step proxy call: geocoding API resolves a location name to `latitude/longitude`, then the forecast API returns daily weather data.
- Geocoding: `GET https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1`
- Forecast: `GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&forecast_days=1&timezone=auto`
- WMO weather codes (returned as `weathercode`) are mapped to human-readable condition strings in the service layer (e.g., `0` → "Clear sky", `61` → "Slight rain").
- Temperatures are returned in Celsius by default; Fahrenheit is derived: `°F = °C × 9/5 + 32`.

**Alternatives considered**:
- OpenWeatherMap — Rejected: requires API key.
- wttr.in — Rejected: JSON schema is unstable and undocumented.
- weather.gov (NWS) — Rejected: US-only coverage.

**WMO Code → Condition mapping (subset)**:

| Code | Condition |
|------|-----------|
| 0 | Clear sky |
| 1–3 | Mainly clear / partly cloudy / overcast |
| 45, 48 | Fog |
| 51, 53, 55 | Drizzle |
| 61, 63, 65 | Rain |
| 71, 73, 75 | Snow |
| 80, 81, 82 | Rain showers |
| 95 | Thunderstorm |

---

## Decision 3: Upstream Currency Rates Service

**Decision**: Use **Frankfurter API** (https://www.frankfurter.app) — free, no API key, historical rates supported.

**Rationale**:
- Fully free with no registration or API key required (satisfies spec assumption).
- Supports historical rates by date: `GET https://api.frankfurter.app/{YYYY-MM-DD}?from={BASE}`
- Supports "latest" rates: `GET https://api.frankfurter.app/latest?from={BASE}`
- Returns structured JSON: `{"amount": 1.0, "base": "USD", "date": "2024-01-15", "rates": {"EUR": 0.918, ...}}`
- Handles market closure days by returning the most recent available rates with the actual date in the response.
- Returns HTTP 404 for dates before the service's data starts (pre-1999); service layer maps this to HTTP 422.

**Date routing logic**:
- If `date` == today → call `/latest?from={base}`
- If `date` < today → call `/{date}?from={base}`
- If `date` > today → reject with HTTP 422 before making any upstream call

**Alternatives considered**:
- Open Exchange Rates — Rejected: requires API key for historical data.
- exchangerate-api.com — Rejected: free tier limits historical access, requires key.
- fixer.io — Rejected: requires API key.

---

## Decision 4: HTTP Client for Upstream Calls

**Decision**: Use **httpx** in synchronous mode (not async).

**Rationale**:
- FastAPI supports both sync and async route handlers. For this simple proxy with no parallelism within a single request, synchronous `httpx` is simpler and sufficient.
- Avoids the complexity of `pytest-asyncio` and async service layers.
- A single `httpx.Client` instance (created per request or as a shared client via FastAPI lifespan) is straightforward to test with `httpx.MockTransport` or `unittest.mock.patch`.
- If concurrency becomes a requirement in future, migration to `httpx.AsyncClient` is a one-line change per service function.

**Alternatives considered**:
- `httpx.AsyncClient` + async routes — Rejected for v1: adds pytest-asyncio complexity for no v1 benefit.
- `requests` library — Rejected: not recommended for use inside async frameworks; httpx is the FastAPI-idiomatic choice.
- `urllib` — Rejected: too low-level, no JSON sugar.

---

## Decision 5: Project Structure

**Decision**: Single-project layout with `src/` package, `routers/`, `services/`, `models/` sub-packages.

**Rationale**: Aligns with Constitution Principle II (Simplicity) and the spec's single-project scope. Business logic lives in services (router handlers call service functions), satisfying Principle II's "business logic MUST live in a service layer" rule.

```
src/
├── main.py              # App factory, lifespan, middleware, startup logging
├── routers/
│   ├── health.py
│   ├── ip.py
│   ├── weather.py
│   └── rates.py
├── services/
│   ├── ip_service.py
│   ├── weather_service.py
│   └── rates_service.py
└── models/
    └── responses.py     # All Pydantic response models

tests/
├── conftest.py          # Shared fixtures (TestClient, mock patches)
├── integration/
│   ├── test_ip.py
│   ├── test_weather.py
│   └── test_rates.py
└── unit/
    ├── test_ip_service.py
    ├── test_weather_service.py
    └── test_rates_service.py
```

---

## Decision 6: Dependency & Tooling Versions

| Package | Version | Role |
|---------|---------|------|
| `fastapi` | ≥ 0.110.0 | Web framework + input validation (Pydantic v2 built-in) |
| `uvicorn[standard]` | ≥ 0.29.0 | ASGI server with access logging |
| `httpx` | ≥ 0.27.0 | Synchronous HTTP client for upstream calls |
| `pytest` | ≥ 8.0.0 | Test runner |
| `pytest-cov` | ≥ 5.0.0 | Coverage reporting |

No additional libraries required for v1. Pydantic v2 is bundled with FastAPI ≥ 0.110.

**Linting / Formatting**: `ruff` (single tool for lint + format, replaces flake8 + black).

---

## Resolved Unknowns

All items from Technical Context were resolved without NEEDS CLARIFICATION:

| Unknown | Resolution |
|---------|------------|
| IP lookup mechanism | Extract from request headers (no upstream call) |
| Weather upstream API | Open-Meteo (free, no key) |
| Currency upstream API | Frankfurter (free, no key) |
| HTTP client | httpx sync |
| Async vs sync | Sync for v1 simplicity |
| WMO code mapping | Defined in service layer lookup table |
