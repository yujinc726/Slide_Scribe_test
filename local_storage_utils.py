import json
from typing import List, Dict, Any

import streamlit as st

# Third-party wrapper around localStorage
try:
    # streamlit-local-storage must be in requirements.txt
    from streamlit_local_storage import LocalStorage  # type: ignore
except ModuleNotFoundError:
    LocalStorage = None  # type: ignore


class _DummyLocalStorage:
    """Fallback that behaves like an in-memory dict when the package is missing.

    This is useful when running in environments where localStorage is not
    available (e.g. unit tests or Streamlit Cloud headless runs).
    """

    def __init__(self):
        self._data: Dict[str, str] = {}

    # API shim that mimics streamlit-local-storage
    def setItem(self, key: str, value: str, **kwargs):  # noqa: N802
        self._data[key] = value

    def getItem(self, key: str, **kwargs):  # noqa: N802
        return self._data.get(key)

    def deleteItem(self, key: str, **kwargs):  # noqa: N802
        self._data.pop(key, None)

    def getAll(self, **kwargs):  # noqa: N802
        return self._data.copy()


# Use real component if available, otherwise dummy fallback.
LOCAL_STORAGE = LocalStorage() if LocalStorage else _DummyLocalStorage()


# -----------------------------------------------------------------------------
# Public helper functions
# -----------------------------------------------------------------------------

def save_records(
    lecture_name: str,
    filename: str,
    records: List[Dict[str, Any]],
) -> None:
    """Save *records* for *lecture_name* under *filename* to browser localStorage.

    Additionally maintains an index of files per lecture so the UI can list
    available JSON logs.
    """
    data_key = f"slide_scribe/{lecture_name}/{filename}"
    index_key = f"slide_scribe_index/{lecture_name}"

    # Serialise records
    json_str = json.dumps(records, ensure_ascii=False)

    # Store the data blob (unique widget key)
    LOCAL_STORAGE.setItem(data_key, json_str, key=f"set_{data_key}")

    # Update index list
    index_raw = LOCAL_STORAGE.getItem(index_key, key=f"idx_get_{lecture_name}")
    try:
        index: List[str] = json.loads(index_raw) if index_raw else []
    except json.JSONDecodeError:
        index = []

    if filename not in index:
        index.insert(0, filename)  # newest first
    LOCAL_STORAGE.setItem(index_key, json.dumps(index, ensure_ascii=False), key=f"idx_set_{lecture_name}")


def get_filenames(lecture_name: str) -> List[str]:
    """Return list of saved JSON filenames for *lecture_name* from localStorage."""
    index_key = f"slide_scribe_index/{lecture_name}"
    index_raw = LOCAL_STORAGE.getItem(index_key, key=f"idx_list_{lecture_name}")
    if not index_raw:
        return []
    try:
        return json.loads(index_raw)
    except json.JSONDecodeError:
        return []


def load_records(lecture_name: str, filename: str) -> List[Dict[str, Any]]:
    """Load records list for given *lecture_name* and *filename* from localStorage."""
    data_key = f"slide_scribe/{lecture_name}/{filename}"
    raw = LOCAL_STORAGE.getItem(data_key, key=f"get_{data_key}")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def delete_records(lecture_name: str, filename: str) -> None:
    """Remove stored records and update the index."""
    data_key = f"slide_scribe/{lecture_name}/{filename}"
    index_key = f"slide_scribe_index/{lecture_name}"
    LOCAL_STORAGE.deleteItem(data_key, key=f"del_{data_key}")

    index_raw = LOCAL_STORAGE.getItem(index_key, key=f"idx_get2_{lecture_name}")
    if not index_raw:
        return
    try:
        index: List[str] = json.loads(index_raw)
    except json.JSONDecodeError:
        index = []
    if filename in index:
        index.remove(filename)
        LOCAL_STORAGE.setItem(index_key, json.dumps(index, ensure_ascii=False), key=f"idx_set2_{lecture_name}") 