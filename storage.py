from datetime import datetime
from typing import List, Dict, Any, Optional

from streamlit_local_storage import LocalStorage

# Single instance shared by whole app
_ls = LocalStorage()

PREFIX = "slide_timer"  # prefix for all keys written by this app


def _make_key(lecture: str, timestamp: Optional[str] = None) -> str:
    """Compose a unique localStorage key for a lecture + timestamp."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"{PREFIX}:{lecture}:{timestamp}"


# ---------------------------------------------------------------------------
# Public helper functions
# ---------------------------------------------------------------------------

def save_records(lecture: str, records: List[Dict[str, Any]]) -> str:
    """Persist a list of slide timer *records* for *lecture* into localStorage.

    Returns the localStorage key that was used to save the data so that the
    caller can keep a reference to it.
    """
    key = _make_key(lecture)
    _ls.setItem(key, records)
    return key


def load_records(key: str) -> List[Dict[str, Any]]:
    """Read the record list that was previously saved under *key*.

    If no data is found, an empty list is returned so that the caller can keep
    existing logic unchanged.
    """
    data = _ls.getItem(key)
    return data or []


def list_record_keys(lecture: str) -> List[str]:
    """Return all localStorage keys for *lecture* (newest first)."""
    prefix = f"{PREFIX}:{lecture}:"
    all_items = _ls.getAll()  # returns a dict-like {key: value}
    keys = [k for k in all_items.keys() if k.startswith(prefix)]
    # Sort so that the most recent (lexicographically larger timestamp) appears first
    keys.sort(reverse=True)
    return keys


# ==========================================================
# Lecture name list helpers (stored once per browser)
# ==========================================================

_LECTURES_KEY = f"{PREFIX}:__lectures__"


def get_lecture_names() -> List[str]:
    """Return the lecture name list stored in localStorage (empty list if none)."""
    names = _ls.getItem(_LECTURES_KEY)
    return names or []


def save_lecture_names(names: List[str]):
    """Persist lecture name list into localStorage."""
    _ls.setItem(_LECTURES_KEY, names)


def delete_record(key: str):
    """Remove a saved record from localStorage."""
    _ls.removeItem(key) 