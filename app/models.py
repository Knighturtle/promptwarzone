from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # jp / en
    language: str = Field(default="jp", index=True, max_length=5)

    name: str = Field(index=True, max_length=50)
    persona: Optional[str] = Field(default=None, max_length=50) # AI人格名
    gen_id: Optional[str] = Field(default=None, index=True)     # 生成バッチID（追跡用）
    depth: int = Field(default=0)                               # 返信深度（0=human, 1=ai reply, 2=ai-ai chain）

    content: str = Field(max_length=2000)

    is_ai: bool = Field(default=False, index=True)

    # 返信先
    reply_to_id: Optional[int] = Field(default=None, index=True)

    # スレッドID（ルート投稿のid）
    thread_id: Optional[int] = Field(default=None, index=True)
    
    # Status Flags
    is_hidden: bool = Field(default=False)
    is_locked: bool = Field(default=False) # Only for threads

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

class BannedIP(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ip: str = Field(index=True)
    reason: Optional[str] = Field(default=None)
    banned_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)

class AIEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    thread_id: Optional[int] = Field(default=None, index=True)
    mode: str = Field(max_length=20) # multi, single, chain
    persona: str = Field(max_length=50)
    ok: bool = Field(default=False)
    error: Optional[str] = Field(default=None)
    latency_ms: int = Field(default=0)


