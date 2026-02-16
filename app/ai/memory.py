from datetime import datetime
from sqlmodel import Session, select
from app.db import engine
from app.models import AIState, AIIncident

class AIMemory:
    def __init__(self):
        pass

    def record_learning(self, key: str, value: str):
        with Session(engine) as session:
            state = session.get(AIState, key)
            if not state:
                state = AIState(key=key, value=value)
            else:
                state.value = value
                state.updated_at = datetime.utcnow()
            session.add(state)
            session.commit()

    def get_proposals(self):
        # In a real system, this would analyze audit logs and incidents
        # to propose policy changes.
        return ["Decrease moderation threshold to 0.7", "Increase reply cooldown"]

    def log_incident(self, target_id: str, reason: str):
        with Session(engine) as session:
            inc = AIIncident(
                target_id=target_id,
                report_reason=reason,
                status="open"
            )
            session.add(inc)
            session.commit()


