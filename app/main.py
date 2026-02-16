import os
from fastapi import FastAPI
from starlette.requests import Request
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse, HTMLResponse, PlainTextResponse
from starlette.staticfiles import StaticFiles
from starlette.staticfiles import StaticFiles
from .renderer import Renderer
from sqlmodel import select

from .db import init_db, get_session
from .models import Post
from .ai.multi_reply import generate_multi_replies
from .ai.chain import maybe_ai_chain
from .jobs import start_scheduler
import asyncio

import re
from app.logging import log_info, log_error

app = FastAPI()

BASE_DIR = os.path.dirname(__file__)
# templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory="static"), name="static")

def _check_lang(lang: str) -> str:
    lang = (lang or "").lower().strip()
    if lang not in ("jp", "en"):
        raise HTTPException(status_code=404, detail="lang not found")
    return lang

@app.on_event("startup")
def on_startup():
    init_db()
    # start_scheduler()
    print("STARTUP: DB initialized & Scheduler started")

@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    with get_session() as session:
        cnt = len(session.exec(select(Post)).all())
    return f"ok posts={cnt}\n"

def build_tree(posts):
    nodes = {p.id: {"post": p, "children": []} for p in posts if p.id is not None}
    roots = []
    for p in posts:
        node = nodes.get(p.id)
        if not node:
            continue
        if p.reply_to_id and p.reply_to_id in nodes:
            nodes[p.reply_to_id]["children"].append(node)
        else:
            roots.append(node)

    def sort_children(n):
        n["children"].sort(key=lambda x: x["post"].created_at)
        for c in n["children"]:
            sort_children(c)

    roots.sort(key=lambda x: x["post"].created_at)
    for r in roots:
        sort_children(r)
    return roots

@app.get("/", response_class=HTMLResponse)
def root_redirect(request: Request):
    return RedirectResponse(url="/jp", status_code=302)

@app.get("/{lang}", response_class=HTMLResponse)
def thread_list(request: Request, lang: str):
    lang = _check_lang(lang)
    with get_session() as session:
        posts = session.exec(
            select(Post).where(Post.language == lang).order_by(Post.created_at.asc())
        ).all()

    by_thread = {}
    for p in posts:
        tid = p.thread_id or p.id
        if tid is None:
            continue
        item = by_thread.get(tid)
        if item is None:
            by_thread[tid] = {
                "thread_id": tid,
                "preview": (p.content or "")[:60].replace("\n", " "),
                "replies": 0,
                "last_at": p.created_at,
                "name": p.name,
            }
        else:
            item["replies"] += 1
            if p.created_at > item["last_at"]:
                item["last_at"] = p.created_at

    threads = sorted(by_thread.values(), key=lambda x: x["last_at"], reverse=True)

    title = "JP Board" if lang == "jp" else "EN Board"
    threads_html = Renderer.render_threads(threads, lang)
    full_html = Renderer.render_index(title, lang, threads_html)
    return HTMLResponse(full_html)

@app.get("/{lang}/t/{thread_id}", response_class=HTMLResponse)
def thread_detail(request: Request, lang: str, thread_id: int):
    lang = _check_lang(lang)
    with get_session() as session:
        posts = session.exec(
            select(Post)
            .where(Post.language == lang)
            .where(Post.thread_id == thread_id)
            .order_by(Post.created_at.asc())
        ).all()

        if not posts:
            root = session.exec(
                select(Post).where(Post.language == lang).where(Post.id == thread_id)
            ).first()
            if root:
                posts = [root]

    if not posts:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    # Check Lock Status (Root post)
    root_post = posts[0]
    is_locked = root_post.is_locked
    
    # Mask Hidden
    for p in posts:
        if p.is_hidden:
            p.content = "[Deleted by Admin]"
            p.name = "[Deleted]"

    tree = build_tree(posts)
    tree_html = Renderer.render_tree(tree, lang)
    title = f"Thread {thread_id}"
    full_html = Renderer.render_thread_page(title, lang, thread_id, tree_html, is_locked)
    return HTMLResponse(full_html)

@app.post("/new")
async def new_post(request: Request):
    form = await request.form()
    lang = form.get("lang", "jp")
    name = form.get("name", "Anonymous")
    content = form.get("content", "")
    ai_multi = form.get("ai_multi", "")
    ai = form.get("ai", "")
    ai_persona = form.get("ai_persona", "")
    reply_to_id = form.get("reply_to_id", "")
    lang = _check_lang(lang)
    name = (name or "").strip()[:50]
    content = (content or "").strip()[:2000]
    
    # SPAM CHECKS
    if not content:
        return RedirectResponse(url=f"/{lang}", status_code=303)
        
    # URL Count check (max 2)
    urls = re.findall(r'https?://', content)
    if len(urls) > 2:
        raise HTTPException(status_code=400, detail="Too many URLs")
        
    # NG Words (Simple list)
    ng_words = ["buy crypto", "free bitcoin", "casino"]
    if any(ng in content.lower() for ng in ng_words):
        raise HTTPException(status_code=400, detail="NG word detected")

    parent_id = None
    reply_to_id = (reply_to_id or "").strip()
    if reply_to_id.isdigit():
        parent_id = int(reply_to_id)

    with get_session() as session:
        thread_id = None
        if parent_id is not None:
            parent = session.exec(select(Post).where(Post.language == lang).where(Post.id == parent_id)).first()
            if parent:
                thread_id = parent.thread_id or parent.id
            else:
                thread_id = None
                parent_id = None

        user_post = Post(
            language=lang,
            name=name or "Anonymous",
            content=content,
            is_ai=False,
            reply_to_id=parent_id,
            thread_id=thread_id,
        )
        session.add(user_post)
        session.commit()
        session.refresh(user_post)

        if parent_id is None:
            user_post.thread_id = user_post.id
            session.add(user_post)
            session.commit()

        tid = user_post.thread_id or user_post.id

        recent = session.exec(
            select(Post)
            .where(Post.language == lang)
            .where(Post.thread_id == tid)
            .order_by(Post.created_at.desc())
        ).all()[:8]
        recent = list(reversed(recent))
        context = "\n".join([f"{('AI-' if p.is_ai else '')}{p.name}: {p.content}" for p in recent if p.content])[:1200]

        # AI処理: 指定人格があるか、ランダム複数か、ランダム単発か
        ai_posts_created = []

        if ai_persona:
            replies = generate_multi_replies(content, lang=lang, context=context, specific_persona=ai_persona)
            if replies:
                 r = replies[0]
                 p = Post(
                    language=lang,
                    name=r["name"],
                    persona=r["name"],
                    content=r["content"],
                    is_ai=True,
                    reply_to_id=user_post.id,
                    thread_id=tid,
                    depth=1
                )
                 session.add(p)
                 ai_posts_created.append(p)
            session.commit()
        elif ai_multi == "1":
            replies = generate_multi_replies(content, lang=lang, context=context)
            for r in replies:
                p = Post(
                    language=lang,
                    name=r["name"],
                    persona=r["name"],
                    content=r["content"],
                    is_ai=True,
                    reply_to_id=user_post.id,
                    thread_id=tid,
                    depth=1
                )
                session.add(p)
                ai_posts_created.append(p)
            session.commit()
        elif ai == "1":
            replies = generate_multi_replies(content, lang=lang, context=context)
            if replies:
                 r = replies[0]
                 p = Post(
                    language=lang,
                    name="Assistant",
                    persona="Assistant",
                    content=r["content"],
                    is_ai=True,
                    reply_to_id=user_post.id,
                    thread_id=tid,
                    depth=1
                )
                 session.add(p)
                 ai_posts_created.append(p)
            session.commit()

        # Refresh IDs
        for p in ai_posts_created:
            session.refresh(p)
        
        # Trigger AI Chain?
        # Only if there was an AI reply. Pick the last one to reply to?
        # Or random? User says "choose target post to reply_to (latest ai reply)"
        if ai_posts_created:
            latest_ai = ai_posts_created[-1]
            # Fire and forget (or await if simple)
            # In production, use BackgroundTasks. For now, await is okay but will slow response.
            # Using asyncio.create_task to make it non-blocking roughly
            asyncio.create_task(maybe_ai_chain(tid, latest_ai.id, lang, depth=latest_ai.depth))

    return RedirectResponse(url=f"/{lang}/t/{tid}", status_code=303)

# ==========================
# ADMIN API
# ==========================


ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "changeme")

def _check_admin(request: Request):
    x_admin_token = request.headers.get("x-admin-token")
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid Admin Token")

@app.post("/admin/hide_post/{post_id}")
async def admin_hide_post(request: Request, post_id: int):
    _check_admin(request)
    with get_session() as session:
        p = session.get(Post, post_id)
        if p:
            p.is_hidden = True
            session.add(p)
            session.commit()
            log_info(f"Admin hidden post {post_id}")
    return {"ok": True}

@app.post("/admin/lock_thread/{thread_id}")
async def admin_lock_thread(request: Request, thread_id: int):
    _check_admin(request)
    with get_session() as session:
        root = session.get(Post, thread_id)
        if root:
            root.is_locked = True
            session.add(root)
            session.commit()
            log_info(f"Admin locked thread {thread_id}")
    return {"ok": True}

@app.post("/admin/ban_ip")
async def admin_ban_ip(request: Request):
    _check_admin(request)
    form = await request.form()
    ip = form.get("ip")
    reason = form.get("reason", "")
    if not ip:
        raise HTTPException(status_code=400, detail="IP required")
    from .models import BannedIP
    from datetime import datetime
    with get_session() as session:
        b = BannedIP(ip=ip, reason=reason, banned_at=datetime.utcnow())
        session.add(b)
        session.commit()
        log_info(f"Admin banned IP {ip}")
    return {"ok": True}




# reload for safety pack verification

