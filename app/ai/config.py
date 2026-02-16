import os
from pydantic_settings import BaseSettings

class AISettings(BaseSettings):
    AI_ENABLED: bool = False
    AI_PROVIDER: str = "openai" # openai, ollama
    AI_MODEL: str = "gpt-3.5-turbo"
    AI_API_KEY: str = ""
    AI_KILL_SWITCH: bool = False
    
    # Ratelimits & Thresholds
    AI_POSTS_PER_HOUR: int = 2
    AI_REPLY_COOLDOWN_SECONDS: int = 600
    AI_SUMMARY_THRESHOLD_POSTS: int = 20
    AI_FLAG_THRESHOLD: float = 0.80

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = AISettings()


