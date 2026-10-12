"""
Services and transport layer socket inspection endpoints.
"""

from fastapi import APIRouter
from app.schemas.service import ServicesResponse
from app.services.service_analyzer import service_analyzer

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=ServicesResponse, summary="Inspect Active Services & Protocols", description="Inspects active transport layer sockets, maps processes, and classifies services.")
def get_services():
    """Retrieve active network sockets grouped by service and process."""
    return service_analyzer.analyze_services()
