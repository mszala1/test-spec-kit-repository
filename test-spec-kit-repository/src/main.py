import sys
from contextlib import asynccontextmanager

import fastapi
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.services.exceptions import InvalidDateError, LocationNotFoundError, UpstreamError


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(
        f"[specify] Python {sys.version.split()[0]} | "
        f"FastAPI {fastapi.__version__} | "
        "Listening on 0.0.0.0:8000"
    )
    yield


app = FastAPI(title="Public API Proxy", lifespan=lifespan)


@app.exception_handler(UpstreamError)
async def upstream_error_handler(request: Request, exc: UpstreamError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": exc.message})


@app.exception_handler(LocationNotFoundError)
async def location_not_found_handler(
    request: Request, exc: LocationNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.message})


@app.exception_handler(InvalidDateError)
async def invalid_date_handler(request: Request, exc: InvalidDateError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.message})


# Routers are registered as each phase is implemented:
# - health router (Phase 6)
# - ip router (Phase 3)
# - weather router (Phase 4)
# - rates router (Phase 5)


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
