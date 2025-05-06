from datetime import datetime
import json
import streamlit as st

# We rely on the third-party component ``streamlit-local-storage``.
# Please make sure the package is added to your environment (``pip install streamlit-local-storage``).
try:
    from streamlit_local_storage import LocalStorage  # type: ignore
except ModuleNotFoundError:
    st.error(
        "streamlit-local-storage 패키지가 설치되지 않았습니다.\n"
        "requirements.txt 에 'streamlit-local-storage' 를 추가하고 다시 배포/실행 해주세요."
    )
    # Fallback dummy implementation so that the rest of the code does not crash when running
    class _DummyLS:  # pragma: no cover
        def getItem(self, *_args, **_kwargs):
            return None

        def setItem(self, *_args, **_kwargs):
            return None

        def deleteItem(self, *_args, **_kwargs):
            return None

    LocalStorage = _DummyLS  # type: ignore


# ------------------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------------------

_local_storage: "LocalStorage | None" = None


def _ls() -> "LocalStorage":
    """Return a **singleton** instance of LocalStorage."""
    global _local_storage
    if _local_storage is None:
        _local_storage = LocalStorage()
    return _local_storage


# Keys used inside the browser storage
LECTURE_NAMES_KEY = "lecture_names"  # list[str]


def _get_from_storage(key: str):
    """Read a raw (JSON encoded) value from browser local-storage.

    Due to the asynchronous nature of streamlit components, the first call might
    give ``None``.  We therefore also check *session_state* for the cached
    value that the component writes there.
    """
    component_key = f"ls_get_{key}"
    try:
        value = _ls().getItem(key, key=component_key)
    except TypeError:
        value = _ls().getItem(key)
    if value in (None, "null"):
        # Component value not available yet – try session_state cache.
        value = st.session_state.get(component_key)
    return value


def _set_in_storage(key: str, raw_value: str):
    """Write a JSON-encoded *raw_value* to browser local-storage."""
    try:
        _ls().setItem(key, raw_value, key=f"ls_set_{key}")
    except TypeError:
        _ls().setItem(key, raw_value)


# ------------------------------------------------------------------------------
# Public helpers – Lecture list handling
# ------------------------------------------------------------------------------

def load_lecture_names() -> list[str]:
    """Return the saved lecture names (browser specific)."""
    value = _get_from_storage(LECTURE_NAMES_KEY)
    if value:
        try:
            return json.loads(value)
        except Exception:
            pass
    return []


def save_lecture_names(lecture_names: list[str]) -> None:
    """Persist *lecture_names* to browser storage."""
    _set_in_storage(LECTURE_NAMES_KEY, json.dumps(lecture_names, ensure_ascii=False))


# ------------------------------------------------------------------------------
# Public helpers – Timer logs handling (per lecture)
# ------------------------------------------------------------------------------

def _logs_key(lecture_name: str) -> str:
    """Return the storage key that holds all logs for *lecture_name*."""
    return f"timer_logs_{lecture_name}"


def _load_logs_dict(lecture_name: str) -> dict[str, list[dict]]:
    """Return dict(file_name -> records list) for *lecture_name*."""
    raw = _get_from_storage(_logs_key(lecture_name))
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {}


def _save_logs_dict(lecture_name: str, logs_dict: dict[str, list[dict]]) -> None:
    _set_in_storage(_logs_key(lecture_name), json.dumps(logs_dict, ensure_ascii=False))


def save_records(lecture_name: str, records: list[dict]) -> str:
    """Save *records* for *lecture_name* and return the generated file name."""
    logs = _load_logs_dict(lecture_name)
    date = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M%S")
    file_name = f"{date}_{timestamp}.json"
    logs[file_name] = records
    _save_logs_dict(lecture_name, logs)
    return file_name


def load_records(lecture_name: str, file_name: str) -> list[dict]:
    """Return timer *records* for (lecture_name, file_name)."""
    logs = _load_logs_dict(lecture_name)
    return logs.get(file_name, [])


def list_json_files(lecture_name: str) -> list[str]:
    """Return available timer-log *file names* for *lecture_name*."""
    return sorted(_load_logs_dict(lecture_name).keys(), reverse=True)


def save_json_file(lecture_name: str, file_name: str, data: list[dict]) -> bool:
    """Overwrite an existing log *file_name* for *lecture_name* with *data*."""
    logs = _load_logs_dict(lecture_name)
    logs[file_name] = data
    _save_logs_dict(lecture_name, logs)
    return True


def delete_json_file(lecture_name: str, file_name: str) -> bool:
    """Delete log *file_name* for *lecture_name* from browser storage."""
    logs = _load_logs_dict(lecture_name)
    if file_name in logs:
        del logs[file_name]
        _save_logs_dict(lecture_name, logs)
        return True
    return False 