import random
import logging
logger = logging.getLogger(__name__)

from sqlmodel import Session, select
from app.db import engine
from app.models import Post, Thread
from app.ai.config import settings
from app.ai.workers import AIWorkers
from app.ai.actions import AIActions

class AIOrchestrator:
    def __init__(self):
        self.workers = AIWorkers()
        self.actions = AIActions()

    def on_new_post(self, post_id: int):
        """
        Triggered when a user creates a new post.
        """

        logger.info(f"ORCHESTRATOR: on_new_post {post_id} called. AI_ENABLED={settings.AI_ENABLED}")
        if not settings.AI_ENABLED:
            return

        with Session(engine) as session:
            post = session.get(Post, post_id)
            if not post or post.is_ai:
                return # Ignore self or missing

            # 1. Moderation
            mod_result = self.workers.moderation_worker(post.body)
            if mod_result.get("score", 0) > settings.AI_FLAG_THRESHOLD:
                print(f"AI: Flagging post {post_id} (Score: {mod_result['score']})")
                self.actions.flag_post(post_id, mod_result.get("reason", "High toxicity"), mod_result.get("score"))
                return # Stop processing if flagged

            # 2. Engagement (Reply decision)
            # Simple heuristic: Only reply to safe posts, randomly, or if directly addressed (not implemented)
            # Check cooldown / rate limit
            # For MVP: Always check for engagement during testing
            # if random.random() < 0.5:
            if True:
                thread = session.get(Thread, post.thread_id)
                # Get context (last 5 posts)
                context_posts = session.exec(
                    select(Post).where(Post.thread_id == post.thread_id).order_by(Post.number.desc()).limit(5)
                ).all()
                # Reverse to chronological
                context_posts.reverse()

                eng_result = self.workers.engagement_worker(thread.title, context_posts)
                logger.info(f"ORCHESTRATOR: eng_result={eng_result}")
                
                if eng_result.get("should_reply"):
                    reply_body = eng_result.get("reply_text")
                    if reply_body:
                        print(f"AI: Replying to thread {thread.id}")
                        self.actions.create_post(
                            thread_id=thread.id,
                            body=reply_body,
                            role="user", # Simulating a user for now
                            score=eng_result.get("confidence", 0.0),
                            reason="Engagement"
                        )

    def process_scheduled_tasks(self):
        """
        Called periodically.
        """
        if not settings.AI_ENABLED:
            return
        # E.g., check for stale threads to bump, or generate summaries.
        pass


