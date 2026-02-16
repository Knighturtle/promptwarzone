import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from .db import init_db, get_session
from .models import Post
from .ai.multi_reply import generate_multi_replies
from .ai.chain import maybe_ai_chain
from .jobs import start_scheduler
import asyncio
