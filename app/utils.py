import os, hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
SECRET = os.getenv("BBS_SECRET", "dev_secret")

def is_sage(mail: str) -> bool:
    return (mail or "").strip().lower() == "sage"

def make_user_id(ip: str, ua: str) -> str:
    # Generates a daily rotating ID based on IP, UA, date, and secret.
    day = datetime.utcnow().strftime("%Y-%m-%d")
    raw = f"{ip}|{ua}|{day}|{SECRET}".encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()
    return h[:8].upper()
