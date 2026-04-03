from fastapi import Request

from src.services.exceptions import UpstreamError


def extract_caller_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first_ip = xff.split(",")[0].strip()
        if first_ip:
            return first_ip

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        stripped_ip = x_real_ip.strip()
        if stripped_ip:
            return stripped_ip

    if request.client and request.client.host:
        return request.client.host

    raise UpstreamError("Could not determine caller IP address")