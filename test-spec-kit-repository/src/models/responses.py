from pydantic import BaseModel


class IpResponse(BaseModel):
    ip: str


class WeatherForecast(BaseModel):
    location: str
    date: str
    condition: str
    temperature_c: float
    temperature_f: float


class ExchangeRates(BaseModel):
    date: str
    base: str
    rates: dict[str, float]


class ErrorResponse(BaseModel):
    detail: str
