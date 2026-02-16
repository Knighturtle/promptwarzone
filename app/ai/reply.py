import os
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

SYSTEM_PROMPT = """あなたはBBSの自動返信AI。
日本語で、短く、丁寧に、具体的な次の一手を返す。
攻撃的/差別/違法/個人情報の要求はしない。
"""

def generate_ai_reply(user_text: str) -> str:
    user_text = (user_text or "").strip()
    if not user_text:
        return "（空の投稿なので返信できません）"

    prompt = f"""{SYSTEM_PROMPT}

ユーザー投稿:
{user_text}

AI返信（2〜5文、短く）:
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 180
        }
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            text = (data.get("response") or "").strip()
            return text if text else "（AIが空返答でした。もう一度投稿してください）"
    except Exception as e:
        # Ollamaが落ちてる/モデル未取得/ポート違い等
        return f"（AI返信エラー: {type(e).__name__}）Ollama起動とモデルを確認してください。"


