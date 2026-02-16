import os
import random
import time
from typing import List, Dict
import httpx
import yaml
from sqlmodel import Session
from app.db import engine
from app.models import AIEvent
# FIX: Adjusted import to absolute path for stability, removed unused loggers
from app.logging import log_info, log_error

# FIX: Safe logger import
try:
    from .logger import log_event
except ImportError:
    def log_event(*a, **k): pass

def safe_log(event, **kwargs):
    try:
        log_event(event, **kwargs)
    except:
        pass

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

BASE_DIR = os.path.dirname(__file__)
JP_PATH = os.path.join(BASE_DIR, "personas_jp.yaml")
EN_PATH = os.path.join(BASE_DIR, "personas_en.yaml")

def _load_yaml(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _ollama(prompt: str, temperature: float, num_predict: int) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
    except Exception as e:
        log_error(f"Ollama Error: {e}")
        raise e

def _generate_core(user_text: str, lang: str, context: str = "", specific_persona: str = "") -> List[Dict[str, str]]:
    start_time = time.time()
    user_text = (user_text or "").strip()
    if not user_text:
        return [{"name": "Anon" if lang == "en" else "風吹けば名無し", "content": "(empty)"}]

    cfg = _load_yaml(EN_PATH if lang == "en" else JP_PATH)
    personas = cfg.get("personas", [])
    settings = cfg.get("settings", {})
    max_replies = int(settings.get("max_replies", 3))
    temperature = float(settings.get("temperature", 0.8))
    num_predict = int(settings.get("num_predict", 180))

    picked = []
    if specific_persona:
        found = next((p for p in personas if p["name"] == specific_persona), None)
        if found:
            picked = [found]
        else:
            random.shuffle(personas)
            picked = personas[:1]
    else:
        random.shuffle(personas)
        picked = personas[:max_replies] if personas else [{"name": "Anon", "role": "short reply"}]

    # If specific_persona is set, we usually want just 1 reply (redundant check but safe)
    if specific_persona:
        picked = picked[:1]

    replies = []
    with Session(engine) as session:
        for p in picked:
            pname = p.get("name", "Anon" if lang == "en" else "名無し")
            role = p.get("role", "")

            if lang == "en":
                system = f"""You are an anonymous message board user.
Write in English only. Short 1-3 lines. Internet-forum vibe. No hate, no harassment, no illegal instructions, no personal data requests.
Your role: {role}
"""
            else:
                system = f"""あなたは匿名掲示板の住人。
日本語のみ。短文1〜3行。2chっぽい空気。ただし差別/誹謗中傷/違法助言/個人情報の要求は禁止。
あなたの役割: {role}
"""

            prompt = f"""{system}

(THREAD CONTEXT)
{context}

(POST)
{user_text}

REPLY:
"""
            # Logging Event Setup
            event = AIEvent(
                mode="specific" if specific_persona else "multi",
                persona=pname,
                ok=False
            )
            
            try:
                t0 = time.time()
                text = _ollama(prompt, temperature=temperature, num_predict=num_predict)
                latency = int((time.time() - t0) * 1000)
                
                if not text:
                    text = "草" if lang != "en" else "lol"
                
                event.ok = True
                event.latency_ms = latency
                log_info(f"AI Success: {pname} ({latency}ms)")
                
            except Exception as e:
                text = f"(AI error: {type(e).__name__})" if lang == "en" else f"（AIエラー: {type(e).__name__}）"
                event.error = str(e)
                event.ok = False
                log_error(f"AI Failed: {pname} - {e}")

            session.add(event)
            session.commit()

            text = text.strip()[:500]
            replies.append({"name": pname, "content": text})

    return replies

def generate_multi_replies(user_text: str, lang: str, context: str = "", specific_persona: str = "") -> List[Dict[str, str]]:
    try:
        log_info("AI multi reply generation started")

        replies = _generate_core(user_text, lang, context, specific_persona)

        log_info(f"AI replies generated: {len(replies)}")
        safe_log("multi_reply_success", count=len(replies))

        return replies

    except Exception as e:
        log_error(f"AI multi reply error: {str(e)}")
        safe_log("multi_reply_error", error=str(e))
        return []

