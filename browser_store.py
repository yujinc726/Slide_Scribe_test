import json
import time, uuid
import streamlit as st
from streamlit_local_storage import LocalStorage

# Single LocalStorage component instance
_ls = LocalStorage()
_PREFIX = "slide_scribe"


def _k(*parts: str) -> str:
    """Generate a namespaced key for LocalStorage."""
    return "::".join([_PREFIX, *parts])


# -----------------------------------------------------------------------------
# Lecture list helpers
# -----------------------------------------------------------------------------

def load_lecture_names() -> list[str]:
    """Return list of lecture names stored in the browser (empty list if none)."""
    raw = _ls.getItem(_k("lectures"))
    return json.loads(raw) if raw else []


def save_lecture_names(names: list[str]):
    """Persist full lecture name list to browser storage."""
    _ls.setItem(_k("lectures"), json.dumps(names))


# -----------------------------------------------------------------------------
# Slide-timer record helpers
# -----------------------------------------------------------------------------

def _record_index_key(lecture: str) -> str:
    return _k("records", lecture, "index")


def _record_data_key(lecture: str, rec_id: str) -> str:
    return _k("records", lecture, rec_id)


def list_record_ids(lecture: str) -> list[str]:
    """Return list of record IDs (latest first) for given lecture."""
    raw = _ls.getItem(_record_index_key(lecture))
    return json.loads(raw) if raw else []


def save_records(lecture: str, records: list[dict]) -> str:
    """Save records list under a new timestamp ID and return that ID."""
    rec_id = time.strftime("%Y-%m-%d_%H%M%S")
    # 1) store the record data
    _ls.setItem(
        _record_data_key(lecture, rec_id),
        json.dumps(records, ensure_ascii=False)
    )
    # 2) update the index
    ids = list_record_ids(lecture)
    if rec_id not in ids:
        ids.insert(0, rec_id)
        _ls.setItem(
            _record_index_key(lecture),
            json.dumps(ids)
        )
    return rec_id


def load_records(lecture: str, rec_id: str) -> list[dict]:
    raw = _ls.getItem(_record_data_key(lecture, rec_id))
    return json.loads(raw) if raw else [] 