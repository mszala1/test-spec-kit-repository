---

description: "Task list for Public API Proxy implementation"
---

# Tasks: Public API Proxy

**Input**: Design documents from `/specs/001-public-api-proxy/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api-contracts.md ✅

**Tests**: Test tasks are included — Constitution Principle III (Test-First) is NON-NEGOTIABLE.
Tests MUST be written and confirmed failing before implementation code for each story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every task description

## Path Conventions

- Source: `src/` at repository root
- Tests: `tests/` at repository root

---

## Phase 1: Setup

**Purpose**: Project initialization and base structure. No user story work begins until this phase is complete.

- [x] T001 Create directory structure: `src/routers/`, `src/services/`, `src/models/`, `tests/integration/`, `tests/unit/`
- [x] T002 [P] Create `requirements.txt` with: `fastapi>=0.110.0`, `uvicorn[standard]>=0.29.0`, `httpx>=0.27.0`, `pytest>=8.0.0`, `pytest-cov>=5.0.0`
- [x] T003 [P] Create `pyproject.toml` with ruff configuration (lint + format target: `src/` and `tests/`)
- [x] T004 [P] Create empty `src/__init__.py`, `src/routers/__init__.py`, `src/services/__init__.py`, `src/models/__init__.py`
- [x] T005 [P] Create empty `tests/__init__.py`, `tests/integration/__init__.py`, `tests/unit/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that ALL user story phases depend on. No user story work begins until this phase is complete.

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete.

- [x] T006 Create `src/models/responses.py` — define all Pydantic response models: `IpResponse`, `WeatherForecast`, `ExchangeRates`, `ErrorResponse` (fields per `data-model.md`)
- [x] T007 [P] Create `src/services/exceptions.py` — define custom exception classes: `UpstreamError(message: str)`, `LocationNotFoundError(location: str)`, `InvalidDateError(message: str)`
- [x] T008 Create `src/main.py` — FastAPI app factory with: lifespan startup log (Python version, FastAPI version, bound address), exception handlers for `UpstreamError` → 502, `LocationNotFoundError` → 422, `InvalidDateError` → 422, router includes (health, ip, weather, rates), and uvicorn entry point
- [x] T009 Create `tests/conftest.py` — shared fixtures: `client` fixture using FastAPI `TestClient`, `mock_httpx` fixture using `unittest.mock.patch` for `httpx.Client.get`

**Checkpoint**: Foundation complete — user story phases can now proceed.

---

## Phase 3: User Story 1 — IP Address Lookup (Priority: P1) 🎯 MVP

**Goal**: `GET /ip` returns the caller's public IPv4 address extracted from request headers. No upstream HTTP call.

**Independent Test**: Start the server, call `GET /ip`, verify the response is `{"ip": "<some-ip>"}` with HTTP 200.

### Tests for User Story 1 (write FIRST — must FAIL before implementation)

> **Write these tests before implementing the service or router. Confirm they fail. Then implement.**

- [ ] T010 [P] [US1] Write integration test `tests/integration/test_ip.py`:
  - `test_get_ip_happy_path`: mock `X-Forwarded-For` header → assert HTTP 200, body `{"ip": "1.2.3.4"}`
  - `test_get_ip_falls_back_to_x_real_ip`: no X-Forwarded-For, set X-Real-IP → assert correct IP returned
  - `test_get_ip_upstream_failure`: no headers, no client host → assert HTTP 502, body has `"detail"` key
- [ ] T011 [P] [US1] Write unit test `tests/unit/test_ip_service.py`:
  - `test_extract_ip_from_x_forwarded_for`: first IP in comma-separated list is returned
  - `test_extract_ip_prefers_x_forwarded_for_over_x_real_ip`
  - `test_extract_ip_falls_back_to_client_host`
  - `test_extract_ip_raises_upstream_error_when_all_sources_absent`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/services/ip_service.py` — function `extract_caller_ip(request: Request) -> str`:
  - Check `X-Forwarded-For` (first IP in comma list), then `X-Real-IP`, then `request.client.host`
  - Raise `UpstreamError("Could not determine caller IP address")` if all sources absent/empty
- [ ] T013 [US1] Implement `src/routers/ip.py` — `GET /ip` router:
  - Call `ip_service.extract_caller_ip(request)`; return `IpResponse(ip=ip)` with HTTP 200
  - Register router in `src/main.py` with prefix `""`
- [ ] T014 [US1] Run tests: `pytest tests/integration/test_ip.py tests/unit/test_ip_service.py -v` — all must pass

**Checkpoint**: `GET /ip` is fully functional and independently testable. User Story 1 complete.

---

## Phase 4: User Story 2 — Today's Weather Forecast (Priority: P2)

**Goal**: `GET /weather?location={name}` returns today's forecast (condition + temperature in °C and °F) via Open-Meteo.

**Independent Test**: Call `GET /weather?location=London` → verify HTTP 200 with `location`, `date`, `condition`, `temperature_c`, `temperature_f` fields. Call with unknown location → HTTP 422. Kill upstream (mock) → HTTP 502.

### Tests for User Story 2 (write FIRST — must FAIL before implementation)

> **Write these tests before implementing the service or router. Confirm they fail. Then implement.**

- [ ] T015 [P] [US2] Write integration test `tests/integration/test_weather.py`:
  - `test_get_weather_happy_path`: mock httpx to return geocoding + forecast responses → assert HTTP 200, all required fields present, `temperature_f` matches derived value
  - `test_get_weather_unknown_location`: mock geocoding to return empty `results` → assert HTTP 422, `"detail"` contains `"Location not found"`
  - `test_get_weather_missing_location_param`: call `/weather` without `location` → assert HTTP 422
  - `test_get_weather_upstream_geocoding_failure`: mock httpx to raise `httpx.RequestError` on geocoding call → assert HTTP 502
  - `test_get_weather_upstream_forecast_failure`: mock geocoding to succeed, mock forecast to raise `httpx.RequestError` → assert HTTP 502
- [ ] T016 [P] [US2] Write unit test `tests/unit/test_weather_service.py`:
  - `test_wmo_code_to_condition_clear_sky`: code 0 → `"Clear sky"`
  - `test_wmo_code_to_condition_rain`: code 61 → `"Slight rain"` (or equivalent)
  - `test_wmo_code_to_condition_unknown_falls_back_to_overcast`
  - `test_celsius_to_fahrenheit_conversion`: known values (0°C → 32°F, 100°C → 212°F)
  - `test_get_forecast_raises_location_not_found_when_geocoding_empty`
  - `test_get_forecast_raises_upstream_error_on_httpx_failure`

### Implementation for User Story 2

- [ ] T017 [US2] Implement `src/services/weather_service.py`:
  - `WMO_CONDITIONS: dict[int, str]` lookup table mapping WMO codes to human-readable strings
  - `celsius_to_fahrenheit(temp_c: float) -> float`: inline derivation, rounded to 1 decimal
  - `get_forecast(location: str) -> WeatherForecast`:
    - Step 1: GET `https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1` via `httpx.get()`
    - On `httpx.RequestError` → raise `UpstreamError("Weather service is currently unavailable")`
    - If `results` list is empty → raise `LocationNotFoundError(location)`
    - Step 2: GET `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&forecast_days=1&timezone=auto`
    - On `httpx.RequestError` → raise `UpstreamError("Weather service is currently unavailable")`
    - Map `weathercode[0]` via `WMO_CONDITIONS`, derive `temperature_f`, return `WeatherForecast`
- [ ] T018 [US2] Implement `src/routers/weather.py` — `GET /weather` router:
  - Query param: `location: str` (FastAPI auto-422s if missing)
  - Call `weather_service.get_forecast(location)`; return `WeatherForecast` with HTTP 200
  - Register router in `src/main.py`
- [ ] T019 [US2] Run tests: `pytest tests/integration/test_weather.py tests/unit/test_weather_service.py -v` — all must pass

**Checkpoint**: `GET /weather` is fully functional and independently testable. User Story 2 complete.

---

## Phase 5: User Story 3 — Currency Exchange Rates (Priority: P3)

**Goal**: `GET /rates?date=YYYY-MM-DD&base=USD` returns exchange rates for that date via Frankfurter API.

**Independent Test**: Call `GET /rates?date=2024-01-15` → HTTP 200 with `date`, `base`, `rates` map. Call with future date → HTTP 422. Call with bad date format → HTTP 422. Mock upstream down → HTTP 502.

### Tests for User Story 3 (write FIRST — must FAIL before implementation)

> **Write these tests before implementing the service or router. Confirm they fail. Then implement.**

- [ ] T020 [P] [US3] Write integration test `tests/integration/test_rates.py`:
  - `test_get_rates_historical_happy_path`: mock httpx with Frankfurter response for past date → assert HTTP 200, `date`/`base`/`rates` all present
  - `test_get_rates_today_happy_path`: mock httpx with Frankfurter `/latest` response → assert HTTP 200
  - `test_get_rates_future_date`: pass tomorrow's date → assert HTTP 422, `"detail"` mentions "future"
  - `test_get_rates_invalid_date_format`: pass `date=not-a-date` → assert HTTP 422
  - `test_get_rates_missing_date_param`: call `/rates` without `date` → assert HTTP 422
  - `test_get_rates_default_base_is_usd`: call without `base` param → upstream called with `from=USD`
  - `test_get_rates_custom_base`: call with `base=EUR` → upstream called with `from=EUR`
  - `test_get_rates_upstream_failure`: mock httpx to raise `httpx.RequestError` → assert HTTP 502
- [ ] T021 [P] [US3] Write unit test `tests/unit/test_rates_service.py`:
  - `test_future_date_raises_invalid_date_error`: date = tomorrow → raises `InvalidDateError`
  - `test_today_date_uses_latest_endpoint`: date = today → URL contains `/latest`
  - `test_historical_date_uses_date_endpoint`: past date → URL contains `/{date}`
  - `test_raises_upstream_error_on_httpx_failure`
  - `test_maps_frankfurter_response_to_exchange_rates_model`

### Implementation for User Story 3

- [ ] T022 [US3] Implement `src/services/rates_service.py`:
  - `get_rates(date_str: str, base: str = "USD") -> ExchangeRates`:
    - Parse `date_str` as `datetime.date`; on `ValueError` → raise `InvalidDateError("Invalid date format, expected YYYY-MM-DD")`
    - If parsed date > `date.today()` → raise `InvalidDateError(f"Future dates are not supported. Requested: {date_str}, today: {date.today()}")`
    - If parsed date == today → url = `https://api.frankfurter.app/latest?from={base}`
    - Else → url = `https://api.frankfurter.app/{date_str}?from={base}`
    - Call via `httpx.get(url)`; on `httpx.RequestError` or non-2xx → raise `UpstreamError("Currency rates service is currently unavailable")`
    - Map upstream JSON (`date`, `base`, `rates`) → return `ExchangeRates`
- [ ] T023 [US3] Implement `src/routers/rates.py` — `GET /rates` router:
  - Query params: `date: str`, `base: str = "USD"`
  - Call `rates_service.get_rates(date, base)`; return `ExchangeRates` with HTTP 200
  - Register router in `src/main.py`
- [ ] T024 [US3] Run tests: `pytest tests/integration/test_rates.py tests/unit/test_rates_service.py -v` — all must pass

**Checkpoint**: `GET /rates` is fully functional and independently testable. User Story 3 complete.

---

## Phase 6: Health Endpoint (Shared Infrastructure)

**Purpose**: The `/health` endpoint is required by Constitution Principle V (Observability) and is not tied to a specific user story.

- [ ] T025 Write integration test `tests/integration/test_health.py`:
  - `test_health_returns_200_with_status_ok`: call `GET /health` → assert HTTP 200, body `{"status": "ok"}`
- [ ] T026 Implement `src/routers/health.py` — `GET /health` router returning `{"status": "ok"}` with HTTP 200. Register in `src/main.py`.
- [ ] T027 Run tests: `pytest tests/integration/test_health.py -v` — must pass

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verification, documentation, and final validation across all user stories.

- [ ] T028 [P] Verify startup logging in `src/main.py` lifespan: confirm Python version, FastAPI version, and bind address are logged on startup (per Constitution Principle V)
- [ ] T029 [P] Verify exception handlers in `src/main.py` cover all three custom exceptions (`UpstreamError`, `LocationNotFoundError`, `InvalidDateError`) and return correct HTTP status codes and `{"detail": "..."}` shape
- [ ] T030 Run full test suite with coverage: `pytest tests/ --cov=src --cov-report=term-missing` — all tests pass, no uncovered service-layer branches
- [ ] T031 [P] Run ruff lint + format check: `ruff check src/ tests/ && ruff format --check src/ tests/` — zero violations
- [ ] T032 [P] Validate quickstart: follow `specs/001-public-api-proxy/quickstart.md` end-to-end — all curl commands return expected responses
- [ ] T033 [P] Confirm auto-generated API docs are accessible at `http://localhost:8000/docs` and all 4 endpoints are listed with correct schemas

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately, all tasks parallelizable
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user story phases
- **US1 (Phase 3)**: Depends on Foundational completion only — independent of US2, US3
- **US2 (Phase 4)**: Depends on Foundational completion only — independent of US1, US3
- **US3 (Phase 5)**: Depends on Foundational completion only — independent of US1, US2
- **Health (Phase 6)**: Depends on Foundational completion only — independent of all stories
- **Polish (Phase 7)**: Depends on all previous phases complete

### Within Each User Story

1. Tests MUST be written and confirmed failing before implementation (T010/T011 before T012–T014, etc.)
2. Service before router (router calls service)
3. Run story tests after implementation to confirm green

### Parallel Opportunities

- All Phase 1 tasks (T001–T005): fully parallel
- Phase 2 tasks: T006, T007 parallel; T008 depends on T006+T007; T009 independent
- Once Phase 2 is done: Phase 3, 4, 5, and 6 can all start in parallel (different files throughout)
- Within each story: test files (T010+T011, T015+T016, T020+T021) are fully parallel to each other
- Phase 7 polish tasks (T028, T029, T031, T032, T033) are fully parallel after T030

---

## Parallel Example: User Story 2

```bash
# Launch test writing in parallel:
Task: "Write integration test tests/integration/test_weather.py (T015)"
Task: "Write unit test tests/unit/test_weather_service.py (T016)"

# Confirm both test files fail, then launch implementation:
Task: "Implement src/services/weather_service.py (T017)"
# Once service is done:
Task: "Implement src/routers/weather.py (T018)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 6: Health endpoint (small, fast, proves app boots)
4. Complete Phase 3: User Story 1 (IP lookup)
5. **STOP and VALIDATE**: `pytest tests/` passes; `curl localhost:8000/ip` returns IP
6. Demo-able MVP: service boots, health check works, IP endpoint works

### Incremental Delivery

1. Setup + Foundational + Health → app boots cleanly
2. Add US1 → `GET /ip` works → MVP ✅
3. Add US2 → `GET /weather` works → Demo-able
4. Add US3 → `GET /rates` works → Feature complete
5. Polish → PR-ready

### Parallel Team Strategy

After Phase 2 is complete:
- Developer A: US1 (Phase 3) + Health (Phase 6)
- Developer B: US2 (Phase 4)
- Developer C: US3 (Phase 5)

---

## Notes

- `[P]` tasks involve different files — no merge conflicts
- `[US?]` label maps each task to its user story for traceability
- Tests MUST fail before implementation (Constitution Principle III — NON-NEGOTIABLE)
- Each story phase is independently completable, testable, and deployable
- Commit after each story phase checkpoint
- Stop at any checkpoint to validate the story independently before proceeding
