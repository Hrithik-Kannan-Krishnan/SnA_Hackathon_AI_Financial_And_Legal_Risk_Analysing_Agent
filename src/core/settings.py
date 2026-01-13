from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    qdrant_path: Path
    sqlite_path: Path
    embed_model: str
    chat_model: str

def get_settings() -> Settings:
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    qdrant_path_str = os.getenv("QDRANT_PATH", "./storage/qdrant")
    sqlite_path_str = os.getenv("SQLITE_PATH", "./storage/sqlite/app.db")
    embed_model = os.getenv("EMBED_MODEL", "nomic-embed-text")
    chat_model = os.getenv("CHAT_MODEL", "qwen2.5:7b")

    qdrant_path = Path(qdrant_path_str).expanduser().resolve()
    sqlite_path = Path(sqlite_path_str).expanduser().resolve()

    qdrant_path.mkdir(parents=True, exist_ok=True)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        ollama_base_url=ollama_base_url.rstrip("/"),
        qdrant_path=qdrant_path,
        sqlite_path=sqlite_path,
        embed_model=embed_model,
        chat_model=chat_model,
    )