# Feature Specification: Public API Proxy

**Feature Branch**: `001-public-api-proxy`
**Created**: 2026-03-25
**Status**: Draft
**Input**: User description: "I'm building a simple web API that will act as a proxy from other public APIs (such as what is my ip address, weather, market data). There should be endpoints for: returning my ip address, returning forecasted weather for today in a given place, returning currency rates for given day"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - IP Address Lookup (Priority: P1)

A caller sends a request to the proxy and receives their own public IP address in the response. No input is required from the caller — the proxy determines the IP from the incoming request and returns it.

**Why this priority**: This is the simplest endpoint with zero input parameters and no external dependencies beyond a single upstream lookup. It provides immediate, demonstrable value and establishes the proxy pattern used by all subsequent stories.

**Independent Test**: Can be fully tested by sending a request to the IP endpoint from a known network and verifying the returned IP matches the caller's public address.

**Acceptance Scenarios**:

1. **Given** the API is running, **When** a caller requests their IP address, **Then** the response contains their public IPv4 address in a structured JSON body with HTTP 200.
2. **Given** the upstream IP lookup service is unavailable, **When** a caller requests their IP address, **Then** the API returns a structured JSON error response (not a raw upstream error) with an appropriate HTTP error status code.

---

### User Story 2 - Today's Weather Forecast (Priority: P2)

A caller provides a location (city name or geographic identifier) and receives a weather forecast for the current day at that location. The forecast includes at minimum the expected condition (e.g., sunny, rainy) and temperature.

**Why this priority**: Weather is the most contextually rich endpoint and represents the core proxy use-case: accepting caller input, forwarding to an upstream service, and returning a normalised response.

**Independent Test**: Can be fully tested by requesting weather for a well-known city and verifying the response contains a forecast with condition and temperature fields, independently of other endpoints.

**Acceptance Scenarios**:

1. **Given** a valid location name, **When** a caller requests today's weather forecast, **Then** the response contains at minimum: location name, date, weather condition description, and temperature, with HTTP 200.
2. **Given** an unrecognised or malformed location name, **When** a caller requests the forecast, **Then** the API returns a structured JSON error response with HTTP 422 and a human-readable description of the issue.
3. **Given** the upstream weather service is unavailable, **When** a caller requests the forecast, **Then** the API returns a structured JSON error response (not a raw upstream error) with HTTP 502.

---

### User Story 3 - Currency Exchange Rates (Priority: P3)

A caller provides a date and receives exchange rates for that date. The rates are returned relative to a base currency (USD by default). The caller may optionally specify the base currency.

**Why this priority**: Currency rates add the dimension of date-based historical data and an optional parameter, building on the proxy pattern established in P1 and P2.

**Independent Test**: Can be fully tested by requesting rates for a specific past date and verifying the response contains a map of currency codes to exchange rates relative to the stated base currency.

**Acceptance Scenarios**:

1. **Given** a valid date (past or today), **When** a caller requests currency rates, **Then** the response contains the date, the base currency, and a set of exchange rate pairs with HTTP 200.
2. **Given** a future date, **When** a caller requests currency rates, **Then** the API returns a structured JSON error with HTTP 422 indicating that future dates are not supported.
3. **Given** an invalid date format, **When** a caller requests currency rates, **Then** the API returns a structured JSON error with HTTP 422 and a field-level description of the validation failure.
4. **Given** the upstream rates service is unavailable, **When** a caller requests currency rates, **Then** the API returns a structured JSON error (not a raw upstream error) with HTTP 502.

---

### Edge Cases

- What happens when the caller's IP cannot be determined (e.g., missing headers in certain proxy/load-balancer configurations)?
- How does the system behave when an upstream API returns a partial or malformed payload?
- What is returned if the requested date for currency rates falls on a weekend or public holiday when markets are closed?
- How does the weather endpoint handle ambiguous location names that match multiple places (e.g., "Springfield")?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose a `GET /ip` endpoint that returns the caller's public IP address in a JSON response.
- **FR-002**: The system MUST expose a `GET /weather` endpoint that accepts a `location` query parameter and returns today's weather forecast in a JSON response.
- **FR-003**: The system MUST expose a `GET /rates` endpoint that accepts a `date` query parameter (ISO 8601 format: `YYYY-MM-DD`) and returns currency exchange rates for that date in a JSON response.
- **FR-004**: The `GET /rates` endpoint MUST accept an optional `base` query parameter specifying the base currency (3-letter ISO 4217 code). When omitted, the base currency MUST default to USD.
- **FR-005**: All endpoints MUST return JSON-formatted responses for both successful and error cases.
- **FR-006**: All error responses MUST include a `detail` field with a human-readable description of the error.
- **FR-007**: Input validation failures MUST return HTTP 422 with field-level error details.
- **FR-008**: Upstream service failures MUST return HTTP 502 with a structured error body; raw upstream error messages or stack traces MUST NOT be exposed to callers.
- **FR-009**: The system MUST expose a `GET /health` endpoint that returns HTTP 200 with `{"status": "ok"}` when the service is operational.
- **FR-010**: The `GET /rates` endpoint MUST reject requests for future dates with HTTP 422.

### Key Entities

- **IpResponse**: Represents the result of a public IP lookup. Key attributes: `ip` (the caller's public IPv4 address).
- **WeatherForecast**: Represents a single-day weather forecast for a location. Key attributes: `location` (resolved place name), `date`, `condition` (human-readable description), `temperature_c` (degrees Celsius), `temperature_f` (degrees Fahrenheit).
- **ExchangeRates**: Represents currency rates for a given date relative to a base currency. Key attributes: `date`, `base` (3-letter currency code), `rates` (map of currency code → exchange rate).
- **ErrorResponse**: Represents any error returned by the API. Key attributes: `detail` (human-readable message).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three proxy endpoints return correct, structured JSON responses for valid inputs 100% of the time under normal operating conditions.
- **SC-002**: Callers receive a meaningful, structured error response (never a raw error or empty body) for any invalid input or upstream failure.
- **SC-003**: The `/health` endpoint responds within 1 second and confirms service availability at any time.
- **SC-004**: All three data endpoints respond to callers in under 3 seconds end-to-end under normal upstream latency conditions.
- **SC-005**: A new developer can call all three endpoints successfully within 10 minutes of starting the service, using only the available documentation.

## Assumptions

- Callers of this API are trusted internal consumers or developers; no authentication or rate limiting is required for v1.
- "Today's weather forecast" means the forecast for the current calendar date in the location's local timezone.
- Currency rates for weekends and public holidays will return the most recent available rates from the upstream provider; it is the upstream provider's responsibility to handle market closure days.
- Ambiguous location names for weather will be resolved by the upstream provider; the proxy returns whichever result the upstream service provides as primary.
- The proxy does not cache upstream responses in v1; caching may be introduced as a future enhancement.
- IPv6 addresses are out of scope for v1; only IPv4 is returned.
- All upstream public APIs are freely accessible without authentication tokens for reasonable usage volumes; API key management is out of scope for v1.
