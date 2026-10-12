"""
Alerts endpoint for network spikes and anomaly notifications.
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.alert import Alert
from app.schemas.settings import AlertsResponse, AlertItem

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertsResponse, summary="Get Network Anomaly Alerts", description="Returns deterministic alerts triggered by bandwidth spikes or traffic anomalies.")
def get_alerts(
    limit: int = Query(20, ge=1, le=100),
    resolved: bool = Query(False, description="Filter by resolved status"),
    db: Session = Depends(get_db),
):
    """Retrieve active or past network telemetry alerts."""
    alerts = (
        db.query(Alert)
        .filter(Alert.resolved == resolved)
        .order_by(Alert.timestamp.desc())
        .limit(limit)
        .all()
    )

    items = [
        AlertItem(
            id=a.id,
            timestamp=a.timestamp.isoformat(),
            type=a.alert_type,
            severity=a.severity,
            message=a.message,
            device_id=a.device_id,
            resolved=a.resolved,
        )
        for a in alerts
    ]

    return {
        "status": "success",
        "alerts_count": len(items),
        "alerts": items,
    }
