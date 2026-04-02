from fastapi import Request

from src.services.exceptions import UpstreamError


def extract_caller_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    raise UpstreamError("Could not determine caller IP address")
