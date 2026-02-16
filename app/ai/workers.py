import json
from app.ai.llm_client import LLMClient
from app.ai.policy import AIPolicy

class AIWorkers:
    def __init__(self):
        self.llm = LLMClient()

    def moderation_worker(self, post_body: str) -> dict:
        """
        Returns {score: float, flag: bool, reason: str}
        """
        sys_prompt = "You are a content moderator for a BBS."
        user_prompt = AIPolicy.get_moderation_prompt(post_body)
        
        try:
            raw = self.llm.chat_completion(sys_prompt, user_prompt, temperature=0.0)
            # Simple JSON cleanup
            raw = raw.strip().replace("```json", "").replace("```", "")
            return json.loads(raw)
        except Exception as e:
            print(f"Moderation Worker Failed: {e}")
            return {"score": 0.0, "flag": False, "reason": "Error"} # Fail safe

    def engagement_worker(self, thread_title: str, context_posts: list) -> dict:
        """
        Returns {should_reply: bool, reply_text: str, confidence: float}
        """
        sys_prompt = "You are a helpful and witty BBS resident."
        user_prompt = AIPolicy.get_engagement_prompt(thread_title, context_posts)

        try:
            raw = self.llm.chat_completion(sys_prompt, user_prompt, temperature=0.7)
            raw = raw.strip().replace("```json", "").replace("```", "")
            data = json.loads(raw)
            return data
        except Exception as e:
            print(f"Engagement Worker Failed: {e}")
            return {"should_reply": False}

    def summary_worker(self, posts: list) -> str:
        # Placeholder for summary logic
        return "Summary not implemented yet."


