import os
from sqlmodel import SQLModel, create_engine, Session

DB_PATH = os.getenv("DB_PATH", "bbs_v2.sqlite3")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)


