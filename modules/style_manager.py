"""
Writing Style Manager Module
Manages writing style profiles, sample tweets, and custom personas
"""
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_user_samples() -> list[str]:
    """Load user's sample tweets from file"""
    path = DATA_DIR / "user_samples.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_user_samples(samples: list[str]):
    """Save user's sample tweets to file"""
    path = DATA_DIR / "user_samples.json"
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)


def load_custom_persona() -> str:
    """Load custom persona/style analysis"""
    path = DATA_DIR / "custom_persona.txt"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def save_custom_persona(persona: str):
    """Save custom persona/style analysis"""
    path = DATA_DIR / "custom_persona.txt"
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(persona)


def load_monitored_accounts() -> list[str]:
    """Load custom monitored accounts"""
    path = DATA_DIR / "monitored_accounts.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_monitored_accounts(accounts: list[str]):
    """Save custom monitored accounts"""
    path = DATA_DIR / "monitored_accounts.json"
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)


def load_post_history() -> list[dict]:
    """Load history of posted tweets"""
    path = DATA_DIR / "post_history.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_post_history(history: list[dict]):
    """Save post history"""
    path = DATA_DIR / "post_history.json"
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_to_post_history(entry: dict):
    """Add a single entry to post history"""
    history = load_post_history()
    history.insert(0, entry)
    # Keep only last 100 entries
    history = history[:100]
    save_post_history(history)


def load_draft_tweets() -> list[dict]:
    """Load saved draft tweets"""
    path = DATA_DIR / "drafts.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_draft_tweets(drafts: list[dict]):
    """Save draft tweets"""
    path = DATA_DIR / "drafts.json"
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(drafts, f, ensure_ascii=False, indent=2)


def add_draft(text: str, topic: str = "", style: str = ""):
    """Add a draft tweet"""
    import datetime
    drafts = load_draft_tweets()
    drafts.insert(0, {
        "text": text,
        "topic": topic,
        "style": style,
        "created_at": datetime.datetime.now().isoformat(),
    })
    drafts = drafts[:50]  # Keep last 50 drafts
    save_draft_tweets(drafts)


def delete_draft(index: int):
    """Delete a draft by index"""
    drafts = load_draft_tweets()
    if 0 <= index < len(drafts):
        drafts.pop(index)
        save_draft_tweets(drafts)
