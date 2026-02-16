import random
import uuid
import asyncio
from sqlmodel import select, Session
from app.db import engine
from app.models import Post
from app.ai.multi_reply import generate_multi_replies
from app.chain_safety import safe_chain

async def maybe_ai_chain(thread_id: int, parent_post_id: int, lang: str = "jp", gen_id: str = None, depth: int = 0):
    if not safe_chain(depth):
        return

    if random.random() > 0.3:
        return

    if not gen_id:
        gen_id = str(uuid.uuid4())

    with Session(engine) as session:
        parent = session.get(Post, parent_post_id)
        if not parent:
            return
        
        recent = session.exec(select(Post).where(Post.thread_id == thread_id).order_by(Post.created_at.desc())).all()[:6]
        recent = list(reversed(recent))
        context = "\n".join([f"{p.name}: {p.content}" for p in recent if p.content])

        replies = generate_multi_replies(parent.content, lang=lang, context=context)
        
        if not replies:
            return

        r = replies[0]

        ai_post = Post(
            language=lang,
            name=r["name"],
            persona=r["name"],
            content=r["content"],
            is_ai=True,
            reply_to_id=parent_post_id,
            thread_id=thread_id,
            gen_id=gen_id,
            depth=depth+1
        )
        session.add(ai_post)
        session.commit()
        session.refresh(ai_post)
        
        await asyncio.sleep(2)
        await maybe_ai_chain(thread_id, ai_post.id, lang, gen_id, depth+1)
