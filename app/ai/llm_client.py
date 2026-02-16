import json
from app.ai.config import settings
# import openai # Uncomment when ready

class LLMClient:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.model = settings.AI_MODEL
        self.api_key = settings.AI_API_KEY

    def chat_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        Unified interface for chat completion.
        Returns raw string content.
        """
        if self.provider == "mock" or not self.api_key:
            return self._mock_response(system_prompt, user_prompt)
        
        if self.provider == "openai":
            return self._openai_chat(system_prompt, user_prompt, temperature)
        
        # Add ollama support here
        return "Error: Unsupported provider"

    def _mock_response(self, system: str, user: str) -> str:
        # Simple heuristic mock responses for testing
        if "moderator" in system.lower():
            if "toxic" in user.lower() or "ban" in user.lower():
                return json.dumps({"score": 0.9, "reason": "Contains toxic keywords (Mock)", "flag": True})
            return json.dumps({"score": 0.1, "reason": "Safe content (Mock)", "flag": False})
        if "resident" in system.lower():
            return json.dumps({"should_reply": True, "reply_text": "AI Reply: This is interesting!", "confidence": 0.9})
        return "Mock response"

    def _openai_chat(self, system: str, user: str, temp: float) -> str:
        # Placeholder for real OpenAI call
        # client = openai.OpenAI(api_key=self.api_key)
        # response = client.chat.completions.create(...)
        # return response.choices[0].message.content
        print(f"OPENAI CALL (Simulated): {user[:50]}...")
        return self._mock_response(system, user)


