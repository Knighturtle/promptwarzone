import json
import hashlib
from datetime import datetime
from sqlmodel import Session
from app.db import engine
from app.models import AIAuditLog

def sanitize_payload(payload: dict) -> str:
    # Minimal sanitization - in real app, remove PII
    return json.dumps(payload, default=str)

def compute_input_hash(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def log_event(
    actor: str,
    event_type: str,
    target_id: str = None,
    rule_id: str = None,
    reason: str = None,
    payload: dict = None,
    content_to_hash: str = None
):
    """
    Writes an audit log entry to the DB.
    Forcefully committed to ensure trace even if action fails later.
    """
    raw_payload = sanitize_payload(payload) if payload else None
    input_h = compute_input_hash(content_to_hash) if content_to_hash else None

    log_entry = AIAuditLog(
        timestamp=datetime.utcnow(),
        actor=actor,
        event_type=event_type,
        target_id=target_id,
        rule_id=rule_id,
        reason=reason,
        input_hash=input_h,
        raw_payload=raw_payload
    )

    try:
        with Session(engine) as session:
            session.add(log_entry)
            session.commit()
    except Exception as e:
        print(f"FAILED TO WRITE AUDIT LOG: {e}")
        # Fallback to file system if DB fails? 
        # For now, print to stderr is enough for MVP.


