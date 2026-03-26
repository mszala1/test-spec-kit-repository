from fastapi import APIRouter, Request

from src.models.responses import IpResponse
from src.services.ip_service import extract_caller_ip

router = APIRouter()


@router.get("/ip", response_model=IpResponse)
def get_ip(request: Request) -> IpResponse:
    ip = extract_caller_ip(request)
    return IpResponse(ip=ip)
