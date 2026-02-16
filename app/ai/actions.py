from sqlmodel import Session, select
from datetime import datetime
from app.db import engine
from app.models import Post, Thread, Board
from app.ai.config import settings
from app.ai.audit import log_event
import logging

logger = logging.getLogger(__name__)

class AIActions:
    def __init__(self):
        self.settings = settings

    def _check_kill_switch(self, action_name: str) -> bool:
        if self.settings.AI_KILL_SWITCH:
            msg = f"AI KILL SWITCH ACTIVE. Blocking {action_name}."
            print(msg)
            logger.warning(msg)
            log_event(
                event_type="KILL_SWITCH",
                actor="System",
                target_id=action_name,
                reason="Kill Switch Enabled"
            )
            return True
        return False

    def create_post(self, thread_id: int, body: str, role: str, score: float, reason: str) -> bool:
        """
        Safely creates a post as AI.
        """
        logger.info(f"ACTIONS: create_post called for thread {thread_id}")
        if self._check_kill_switch("create_post"):
            return False

        with Session(engine) as session:
            # Verify thread exists & not locked
            thread = session.get(Thread, thread_id)
            if not thread or thread.is_locked:
                return False

            # Get next number
            last = session.exec(
                select(Post).where(Post.thread_id == thread_id).order_by(Post.number.desc())
            ).first()
            next_no = (last.number + 1) if last else 1

            # Create Post
            post = Post(
                thread_id=thread_id,
                number=next_no,
                name=f"AI ({role})", # Transparent naming
                body=body,
                user_id="AI_BOT", 
                created_at=datetime.utcnow(),
                is_ai=True,
                ai_role=role,
                ai_score=score,
                ai_reason=reason
            )
            session.add(post)
            session.commit()
            
            # Audit
            log_event(
                actor=role,
                event_type="POST_CREATE",
                target_id=f"post:{post.id}",
                reason=reason,
                payload={"thread_id": thread_id, "score": score},
                content_to_hash=body
            )
            return True

    def flag_post(self, post_id: int, reason: str, score: float) -> bool:
        """
        Flags a post (does NOT delete).
        """
        if self._check_kill_switch("flag_post"):
            return False
        
        # In a real app, this might update a 'status' field or insert into a 'Flag' table.
        # For this MVP, we just log the flag event strongly.
        log_event(
            actor="moderator",
            event_type="POST_FLAG",
            target_id=f"post:{post_id}",
            reason=reason,
            payload={"score": score}
        )
        return True

    # DELETE / BAN are strictly unimplemented/forbidden here.


