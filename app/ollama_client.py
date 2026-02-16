from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

try:
    import ollama as ollama_py  # pip install ollama
except Exception:
    ollama_py = None

Message = Dict[str, str]  # {"role": "...", "content": "..."}

class OllamaClient:
    def __init__(
        self,
        mode: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: float = 120.0,
    ) -> None:
        self.mode = (mode or os.getenv("OLLAMA_MODE", "http")).lower()
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.timeout_s = timeout_s

    def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.8,
        top_p: float = 0.9,
        num_predict: int = 256,
        seed: Optional[int] = None,
    ) -> str:
        use_model = model or self.model

        if self.mode == "py":
            return self._chat_py(
                model=use_model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                num_predict=num_predict,
                seed=seed,
            )

        return self._chat_http(
            model=use_model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            num_predict=num_predict,
            seed=seed,
        )

    def _chat_http(
        self,
        model: str,
        messages: List[Message],
        temperature: float,
        top_p: float,
        num_predict: int,
        seed: Optional[int],
    ) -> str:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": num_predict,
            },
        }
        if seed is not None:
            payload["options"]["seed"] = seed

        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()

        return (data.get("message") or {}).get("content", "").strip()

    def _chat_py(
        self,
        model: str,
        messages: List[Message],
        temperature: float,
        top_p: float,
        num_predict: int,
        seed: Optional[int],
    ) -> str:
        if ollama_py is None:
            raise RuntimeError("Pythonのollamaライブラリが見つかりません。`pip install ollama` を実行してください。")

        options: Dict[str, Any] = {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": num_predict,
        }
        if seed is not None:
            options["seed"] = seed

        res = ollama_py.chat(
            model=model,
            messages=messages,
            options=options,
            stream=False,
        )
        return (res.get("message") or {}).get("content", "").strip()
