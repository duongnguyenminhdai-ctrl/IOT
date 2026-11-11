import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Incident
from app.config import settings

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

@router.get("/")
def get_incidents(limit: int = 50, skip: int = 0, db: Session = Depends(get_db)):
    """Retrieves list of incident history logs sorted by most recent first."""
    items = db.query(Incident).order_by(Incident.timestamp.desc()).offset(skip).limit(limit).all()
    results = []
    for item in items:
        snapshot_filename = os.path.basename(item.snapshot_path) if item.snapshot_path else None
        results.append({
            "id": item.id,
            "timestamp": item.timestamp.strftime("%Y-%m-%d %H:%M:%S") if item.timestamp else "",
            "event_type": item.event_type,
            "description": item.description,
            "person_id": item.person_id,
            "dwell_time": item.dwell_time,
            "snapshot_url": f"/api/incidents/snapshot/{snapshot_filename}" if snapshot_filename else None
        })
    return {"total": len(results), "incidents": results}

@router.get("/snapshot/{filename}")
def get_snapshot_file(filename: str):
    """Serves annotated incident snapshots."""
    file_path = os.path.join(settings.SNAPSHOT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return FileResponse(file_path, media_type="image/jpeg")

@router.delete("/clear")
def clear_incidents(db: Session = Depends(get_db)):
    """Clears all logged incidents."""
    db.query(Incident).delete()
    db.commit()
    return {"status": "success", "message": "All incident logs cleared."}

