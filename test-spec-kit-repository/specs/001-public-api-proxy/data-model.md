# Data Model: Public API Proxy

**Branch**: `001-public-api-proxy` | **Phase**: 1 | **Date**: 2026-03-25

> This project has no persistent storage. All models below are request/response shapes (Pydantic models).
> There are no database entities, migrations, or schemas.

---

## Response Models

### IpResponse

Returned by `GET /ip`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ip` | `str` | Yes | Caller's public IPv4 address (e.g., `"93.184.216.34"`) |

**Validation rules**:
- `ip` MUST be a non-empty string.
- Format is determined by the upstream extraction logic; no regex validation applied (avoids false rejects behind NAT/proxy).

---

### WeatherForecast

Returned by `GET /weather`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `location` | `str` | Yes | Resolved place name returned by the geocoding service |
| `date` | `str` | Yes | ISO 8601 date string (`YYYY-MM-DD`) for the forecast |
| `condition` | `str` | Yes | Human-readable weather description (e.g., `"Partly cloudy"`) |
| `temperature_c` | `float` | Yes | Maximum daytime temperature in degrees Celsius |
| `temperature_f` | `float` | Yes | Maximum daytime temperature in degrees Fahrenheit (derived: `°C × 9/5 + 32`) |

**Validation rules**:
- `location` query parameter MUST be a non-empty string.
- If the geocoding upstream returns zero results, the service raises a 422 error with `detail: "Location not found: {location}"`.

---

### ExchangeRates

Returned by `GET /rates`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | `str` | Yes | ISO 8601 date string of the rates (`YYYY-MM-DD`). May differ from requested date on market-closure days (upstream behaviour). |
| `base` | `str` | Yes | 3-letter ISO 4217 base currency code (e.g., `"USD"`) |
| `rates` | `dict[str, float]` | Yes | Map of currency code → exchange rate relative to `base` |

**Query parameters**:
- `date` (required): ISO 8601 format `YYYY-MM-DD`. Future dates rejected with HTTP 422.
- `base` (optional, default `"USD"`): 3-letter ISO 4217 code.

**Validation rules**:
- `date` MUST match `YYYY-MM-DD` format; malformed dates return HTTP 422.
- `date` MUST NOT be in the future (compared to UTC today); future dates return HTTP 422.
- `base` MUST be 3 uppercase letters if provided; invalid codes are forwarded to upstream which returns an error — service maps this to HTTP 422.

---

### ErrorResponse

Returned by all endpoints on any error (4xx or 5xx).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `detail` | `str` | Yes | Human-readable error message. Never contains stack traces or raw upstream error bodies. |

FastAPI's default validation error shape also uses `detail` (as a list for 422s); no custom override needed.

---

## Model Relationships

```
Request                 Service call               Response model
─────────────────────────────────────────────────────────────────
GET /ip               → IP header extraction    → IpResponse
GET /weather          → Open-Meteo geocoding
                      → Open-Meteo forecast     → WeatherForecast
GET /rates            → Frankfurter API         → ExchangeRates
any error             → exception handler       → ErrorResponse
```

---

## Internal Service Exceptions

These are Python exceptions raised within service modules and caught by FastAPI exception handlers in `main.py`. They are **not** response models but are documented here for completeness.

| Exception | HTTP Status | Triggered when |
|-----------|-------------|----------------|
| `UpstreamError` | 502 | Any upstream HTTP call fails or returns a non-2xx response |
| `LocationNotFoundError` | 422 | Geocoding returns zero results for a location name |
| `InvalidDateError` | 422 | Date is in the future or malformed |
