import json
from datetime import datetime
import streamlit as st
from streamlit_local_storage import LocalStorage

"""Utility helpers that store and retrieve Slide-Scribe data in the browser's
localStorage instead of Streamlit-Cloud shared disk.

The rest of the application continues to work with the *same* path strings it
previously used for JSON files (e.g. "timer_logs/<lecture>/<file>.json").  We
simply use those strings as unique keys inside the browser storage, keeping the
existing UI and logic almost untouched.
"""

__all__ = [
    "load_lecture_names",
    "save_lecture_names",
    "get_existing_json_files",
    "save_records_to_json",
    "load_records_from_json",
    "ls_set",
    "ls_get",
    "ls_delete",
    "ls_get_all",
]

_ls = LocalStorage()

PREFIX = "slidescribe_"  # prevent collision with other apps running on same host
LECTURE_NAMES_KEY = f"{PREFIX}lecture_names"

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def ls_set(key: str, value):
    """Save *value* under *key* (JSON-encoded) in browser localStorage."""
    _ls.setItem(key, _json_dumps(value))


def ls_get(key: str, default=None):
    """Load JSON data stored for *key*.  Returns *default* if missing/empty."""
    raw = _ls.getItem(key)
    if raw in (None, "", "null"):
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def ls_get_all() -> dict:
    """Return *all* localStorage items as {key: python-obj} dict."""
    raw = _ls.getAll()
    if not raw:
        return {}
    decoded = {}
    for k, v in raw.items():
        try:
            decoded[k] = json.loads(v)
        except Exception:
            decoded[k] = v
    return decoded


def ls_delete(key: str):
    """Remove *key* from localStorage (if present)."""
    # streamlit-local-storage uses deleteItem / removeItem in recent versions
    try:
        _ls.deleteItem(key)
    except AttributeError:
        try:
            _ls.removeItem(key)
        except Exception:
            pass

# ---------------------------------------------------------------------------
# High-level domain helpers (lecture names, timer logs …)
# ---------------------------------------------------------------------------

def load_lecture_names():
    return ls_get(LECTURE_NAMES_KEY, default=[])


def save_lecture_names(lecture_names: list[str]):
    ls_set(LECTURE_NAMES_KEY, lecture_names)


def _make_log_key(lecture: str, filename: str) -> str:
    """Return the storage key for a given lecture/filename pair."""
    return f"timer_logs/{lecture}/{filename}"


def get_existing_json_files(lecture_name: str):
    if not lecture_name:
        return []
    prefix = f"timer_logs/{lecture_name}/"
    all_items = ls_get_all().keys()
    files = [k for k in all_items if k.startswith(prefix) and k.endswith(".json")]
    return sorted(files, reverse=True)


def save_records_to_json(lecture_name: str, records: list):
    """Store *records* for given lecture as a new timestamped entry.

    Returns the storage key (same format as the old file path).
    """
    date = datetime.now().strftime("%Y-%m-%d")
    ts = datetime.now().strftime("%H%M%S")
    filename = f"{date}_{ts}.json"
    key = _make_log_key(lecture_name, filename)
    ls_set(key, records)
    return key


def load_records_from_json(file_path: str):
    return ls_get(file_path, default=[]) 