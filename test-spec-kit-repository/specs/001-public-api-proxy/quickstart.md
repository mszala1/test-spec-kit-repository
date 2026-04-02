# Quickstart: Public API Proxy

**Branch**: `001-public-api-proxy` | **Date**: 2026-03-25

Get the service running and verify all three endpoints in under 10 minutes.

---

## Prerequisites

- Python 3.11 or later (`python --version`)
- pip (`pip --version`)
- Internet access (for upstream API calls to Open-Meteo and Frankfurter)

---

## 1. Set Up the Environment

```bash
# From the repository root
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Start the Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Expected startup output:

```
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     [specify] Python 3.11.x | FastAPI x.x.x | Listening on 0.0.0.0:8000
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 3. Verify Health

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status": "ok"}
```

---

## 4. Get Your IP Address

```bash
curl http://localhost:8000/ip
```

Expected:

```json
{"ip": "93.184.216.34"}
```

---

## 5. Get Today's Weather

```bash
curl "http://localhost:8000/weather?location=London"
```

Expected:

```json
{
  "location": "London",
  "date": "2026-03-25",
  "condition": "Partly cloudy",
  "temperature_c": 12.4,
  "temperature_f": 54.3
}
```

Try other locations:

```bash
curl "http://localhost:8000/weather?location=Tokyo"
curl "http://localhost:8000/weather?location=New+York"
```

---

## 6. Get Currency Rates

```bash
# Today's rates (USD base)
curl "http://localhost:8000/rates?date=2026-03-25"

# Historical rates
curl "http://localhost:8000/rates?date=2024-01-15"

# Different base currency
curl "http://localhost:8000/rates?date=2026-03-25&base=EUR"
```

Expected:

```json
{
  "date": "2026-03-25",
  "base": "USD",
  "rates": {
    "EUR": 0.918,
    "GBP": 0.791,
    "JPY": 151.23
  }
}
```

---

## 7. Run the Tests

```bash
# All tests
pytest tests/ -v

# Integration tests only
pytest tests/integration/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage report
pytest tests/ --cov=src --cov-report=term-missing
```

All tests MUST pass before any PR is merged.

---

## Error Scenarios to Verify

```bash
# Unknown location → 422
curl "http://localhost:8000/weather?location=Zzyzx"

# Future date → 422
curl "http://localhost:8000/rates?date=2099-01-01"

# Malformed date → 422
curl "http://localhost:8000/rates?date=not-a-date"

# Missing required parameter → 422
curl "http://localhost:8000/weather"
```

---

## Interactive API Docs

FastAPI provides auto-generated docs at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
