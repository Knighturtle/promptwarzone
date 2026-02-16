from app.ai.config import settings

class AIPolicy:
    # Static constraints
    MAX_REPLY_LENGTH = 300
    FORBIDDEN_WORDS = ["delete", "ban", "kill"] # Simple keyword filter

    @staticmethod
    def get_moderation_prompt(post_body: str) -> str:
        return f"""
        Analyze the following BBS post for toxicity, spam, and policy violations.
        Return strictly valid JSON: {{"score": float (0-1), "flag": bool, "reason": "short string"}}
        
        Post: "{post_body[:1000]}"
        """

    @staticmethod
    def get_engagement_prompt(thread_title: str, context_posts: list) -> str:
        context_str = "\n".join([f"{p.id}: {p.body[:200]}" for p in context_posts])
        return f"""
        You are a participant in a threaded bulletin board.
        Thread Title: {thread_title}
        
        Context:
        {context_str}
        
        Decide if you should reply to add value. Do not reply if the conversation is closed or low quality.
        Return strictly valid JSON: {{"should_reply": bool, "reply_text": "string (or null)", "confidence": float}}
        """


