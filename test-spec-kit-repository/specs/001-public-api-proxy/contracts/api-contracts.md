# API Contracts: Public API Proxy

**Branch**: `001-public-api-proxy` | **Phase**: 1 | **Date**: 2026-03-25  
**Base URL**: `http://localhost:8000` (local dev)

All requests and responses use `Content-Type: application/json`.  
No authentication required.

---

## GET /health

Health check endpoint. Returns service operational status.

### Request

```
GET /health
```

No parameters.

### Responses

#### 200 OK — Service healthy

```json
{
  "status": "ok"
}
```

---

## GET /ip

Returns the caller's public IPv4 address as seen by the proxy.

### Request

```
GET /ip
```

No parameters.

### Responses

#### 200 OK — IP resolved

```json
{
  "ip": "93.184.216.34"
}
```

#### 502 Bad Gateway — IP could not be determined

```json
{
  "detail": "Could not determine caller IP address"
}
```

---

## GET /weather

Returns today's weather forecast for a given location.

### Request

```
GET /weather?location={location}
```

#### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `location` | string | Yes | City name or geographic identifier (e.g., `"London"`, `"New York"`, `"Paris, FR"`) |

### Responses

#### 200 OK — Forecast retrieved

```json
{
  "location": "London",
  "date": "2026-03-25",
  "condition": "Partly cloudy",
  "temperature_c": 12.4,
  "temperature_f": 54.3
}
```

#### 422 Unprocessable Entity — Missing or invalid input

```json
{
  "detail": "location query parameter is required"
}
```

Or when location not found by geocoding:

```json
{
  "detail": "Location not found: Zzyzx"
}
```

#### 502 Bad Gateway — Upstream weather service unavailable

```json
{
  "detail": "Weather service is currently unavailable"
}
```

---

## GET /rates

Returns currency exchange rates for a given date relative to a base currency.

### Request

```
GET /rates?date={YYYY-MM-DD}&base={BASE}
```

#### Query Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `date` | string | Yes | — | Date in `YYYY-MM-DD` format. Must not be in the future. |
| `base` | string | No | `"USD"` | 3-letter ISO 4217 base currency code (e.g., `"EUR"`, `"GBP"`) |

### Responses

#### 200 OK — Rates retrieved

```json
{
  "date": "2026-03-25",
  "base": "USD",
  "rates": {
    "EUR": 0.918,
    "GBP": 0.791,
    "JPY": 151.23,
    "CHF": 0.903
  }
}
```

> Note: `date` in the response may differ from the requested date if the requested date
> falls on a weekend or public holiday (upstream returns the most recent available rates).

#### 422 Unprocessable Entity — Invalid or future date

Future date:

```json
{
  "detail": "Future dates are not supported. Requested: 2027-01-01, today: 2026-03-25"
}
```

Malformed date:

```json
{
  "detail": [
    {
      "loc": ["query", "date"],
      "msg": "invalid date format, expected YYYY-MM-DD",
      "type": "value_error"
    }
  ]
}
```

#### 502 Bad Gateway — Upstream rates service unavailable

```json
{
  "detail": "Currency rates service is currently unavailable"
}
```

---

## Error Shape Summary

All error responses follow this contract:

```json
{
  "detail": "<human-readable message>"
}
```

For FastAPI's built-in validation errors (query param type mismatches), `detail` is a list of
field-level error objects — this is FastAPI's standard 422 shape and is intentionally preserved.

---

## Upstream Dependencies (informational)

| Endpoint | Upstream | URL pattern |
|----------|----------|-------------|
| `GET /ip` | None — header extraction | `request.headers["X-Forwarded-For"]` |
| `GET /weather` | Open-Meteo geocoding | `https://geocoding-api.open-meteo.com/v1/search?name={loc}&count=1` |
| `GET /weather` | Open-Meteo forecast | `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&forecast_days=1&timezone=auto` |
| `GET /rates` (today) | Frankfurter | `https://api.frankfurter.app/latest?from={base}` |
| `GET /rates` (historical) | Frankfurter | `https://api.frankfurter.app/{date}?from={base}` |
