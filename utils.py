# utils.py
import os
import streamlit as st
import secrets
from typing import Optional, List
import json
from datetime import datetime

# ---------- Supabase integration ----------
try:
    from supabase import create_client, Client  # type: ignore
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


def _sanitize_for_path(text: str) -> str:
    """Sanitize a string so it can be safely used as a directory name."""
    # Replace problematic characters with underscore
    return ''.join(c if c.isalnum() or c in ('-', '_') else '_' for c in text)


def _get_streamlit_email() -> Optional[str]:
    """Return the current user's email if available via st.user or experimental_user."""
    # Streamlit >=1.49 uses st.user, older versions used st.experimental_user
    email = None
    if hasattr(st, "user"):
        email = getattr(st.user, "email", None)
    if email is None and hasattr(st, "experimental_user"):
        # Fallback for older versions
        exp_user = getattr(st, "experimental_user", None)
        if exp_user is not None:
            email = getattr(exp_user, "email", None)
    return email


def get_user_id() -> str:
    """Return a stable identifier for the current user.

    If Streamlit provides an email (logged-in Community Cloud users), use a
    sanitized version of that. Otherwise, create (or reuse) an anonymous ID
    stored in session_state. This ensures the same user gets the same folder
    across reruns, while different users do not collide.
    """
    email = _get_streamlit_email()
    if email:
        return _sanitize_for_path(email.lower())

    # Anonymous or local user – use a random token stored in the browser
    if "anonymous_user_id" not in st.session_state:
        st.session_state["anonymous_user_id"] = secrets.token_hex(8)
    return f"guest_{st.session_state['anonymous_user_id']}"


def get_user_data_dir() -> str:
    """Return the root directory for storing all data for this user."""
    user_id = get_user_id()
    base_dir = os.path.join("user_data", user_id)
    # Ensure directory exists
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def get_timer_logs_dir() -> str:
    """Return the path to this user's timer_logs directory, creating it if needed."""
    path = os.path.join(get_user_data_dir(), "timer_logs")
    os.makedirs(path, exist_ok=True)
    return path


def get_lecture_names_file() -> str:
    """Return the file path used to persist lecture names for this user."""
    return os.path.join(get_user_data_dir(), "lecture_names.json")


def load_lecture_names() -> List[str]:
    """Return a list of lecture names for this user.

    The function first checks for a JSON file of user-managed lecture names.
    If it does not exist, it falls back to enumerating directories inside the
    user's timer_logs folder (for backward compatibility).
    """
    names_file = get_lecture_names_file()
    if os.path.exists(names_file):
        try:
            with open(names_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass  # Fall back to directory enumeration

    # Fallback: list directories
    timer_logs_dir = get_timer_logs_dir()
    return [d for d in os.listdir(timer_logs_dir) if os.path.isdir(os.path.join(timer_logs_dir, d))]


def save_lecture_names(lecture_names: List[str]):
    """Persist lecture names for this user."""
    names_file = get_lecture_names_file()
    try:
        with open(names_file, "w", encoding="utf-8") as f:
            json.dump(lecture_names, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"강의 이름 저장 중 오류: {e}")


def ensure_directory(path: str):
    """Create the directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _get_supabase_client():
    """Create or return a cached Supabase client using secrets.toml creds."""
    if not SUPABASE_AVAILABLE:
        st.error("supabase-py 라이브러리가 설치되지 않았습니다. requirements.txt 에 supabase 포함 여부를 확인하세요.")
        raise RuntimeError("supabase not available")
    if 'supabase_client' not in st.session_state:
        try:
            url = st.secrets['supabase']['url']
            key = st.secrets['supabase']['key']
        except Exception:
            st.error("secrets.toml 에 'supabase.url' 과 'supabase.key' 항목을 추가하세요.")
            raise
        st.session_state['supabase_client'] = create_client(url, key)
    return st.session_state['supabase_client']


# Storage buckets (미리 Supabase 프로젝트에서 생성 필요)
LOG_BUCKET = "timer-logs"
META_BUCKET = "slide-meta"


def _upload_json_to_supabase(bucket: str, path: str, data: dict):
    import io, json as _json
    client = _get_supabase_client()
    buffer = io.BytesIO(_json.dumps(data, ensure_ascii=False, indent=2).encode())
    res = client.storage.from_(bucket).upload(path, buffer, upsert=True, content_type="application/json")
    if res.get("error"):
        raise RuntimeError(res["error"])


def _download_json_from_supabase(bucket: str, path: str):
    client = _get_supabase_client()
    try:
        resp = client.storage.from_(bucket).download(path)
        # supabase-py returns bytes
        return json.loads(resp.decode())
    except Exception as e:
        st.error(f"Supabase 다운로드 오류: {e}")
        return None


def _list_json_files_supabase(bucket: str, prefix: str):
    client = _get_supabase_client()
    try:
        items = client.storage.from_(bucket).list(path=prefix)
        # returns list of dicts with 'name'
        return [item["name"] for item in items]
    except Exception as e:
        st.error(f"Supabase 목록 조회 오류: {e}")
        return []


# ----------------- Timer records helpers -----------------
_RECORD_DATE_FMT = "%Y-%m-%d"
_RECORD_TIME_FMT = "%H%M%S"  # e.g., 143015


def _build_record_filename() -> str:
    now = datetime.now()
    date = now.strftime(_RECORD_DATE_FMT)
    ts = now.strftime(_RECORD_TIME_FMT)
    return f"{date}_{ts}.json"


# ---------- Supabase based implementations ----------

def _supabase_save_timer_records(lecture_name: str, records: list) -> str:
    filename = _build_record_filename()
    path = f"{get_user_id()}/{lecture_name}/{filename}"
    _upload_json_to_supabase(LOG_BUCKET, path, records)
    return filename  # we return filename so caller can construct full path if needed


def _supabase_list_timer_files(lecture_name: str):
    prefix = f"{get_user_id()}/{lecture_name}"
    names = _list_json_files_supabase(LOG_BUCKET, prefix)
    # _list_json_files_supabase returns names relative to prefix, or absolute depending. We normalize.
    return [os.path.basename(n) for n in names if n.endswith('.json')]


def _supabase_load_timer_records(lecture_name: str, filename: str):
    path = f"{get_user_id()}/{lecture_name}/{filename}"
    return _download_json_from_supabase(LOG_BUCKET, path) or []


def _supabase_delete_timer_record(lecture_name: str, filename: str):
    client = _get_supabase_client()
    full_path = f"{get_user_id()}/{lecture_name}/{filename}"
    client.storage.from_(LOG_BUCKET).remove(full_path)


# ---------- Local fallback implementations ----------

def _local_save_timer_records(lecture_name: str, records: list) -> str:
    ensure_directory(os.path.join(get_timer_logs_dir(), lecture_name))
    filename = _build_record_filename()
    file_path = os.path.join(get_timer_logs_dir(), lecture_name, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return filename


def _local_list_timer_files(lecture_name: str):
    dir_path = os.path.join(get_timer_logs_dir(), lecture_name)
    if not os.path.exists(dir_path):
        return []
    return [f for f in os.listdir(dir_path) if f.endswith('.json')]


def _local_load_timer_records(lecture_name: str, filename: str):
    file_path = os.path.join(get_timer_logs_dir(), lecture_name, filename)
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _local_delete_timer_record(lecture_name: str, filename: str):
    file_path = os.path.join(get_timer_logs_dir(), lecture_name, filename)
    if os.path.exists(file_path):
        os.remove(file_path)


# ---------- Public API ----------


def save_timer_records(lecture_name: str, records: list) -> str:
    """Save timer records and return the filename saved."""
    if SUPABASE_AVAILABLE:
        try:
            return _supabase_save_timer_records(lecture_name, records)
        except Exception as e:
            st.warning(f"Supabase 저장 실패, 로컬에 저장합니다: {e}")
    return _local_save_timer_records(lecture_name, records)


def list_timer_record_files(lecture_name: str):
    if SUPABASE_AVAILABLE:
        try:
            return _supabase_list_timer_files(lecture_name)
        except Exception as e:
            st.warning(f"Supabase 목록 실패, 로컬로 대체: {e}")
    return _local_list_timer_files(lecture_name)


def load_timer_records(lecture_name: str, filename: str):
    if SUPABASE_AVAILABLE:
        try:
            data = _supabase_load_timer_records(lecture_name, filename)
            if data is not None:
                return data
        except Exception as e:
            st.warning(f"Supabase 로드 실패, 로컬로 대체: {e}")
    return _local_load_timer_records(lecture_name, filename)


def delete_timer_record(lecture_name: str, filename: str):
    if SUPABASE_AVAILABLE:
        try:
            _supabase_delete_timer_record(lecture_name, filename)
            return
        except Exception as e:
            st.warning(f"Supabase 삭제 실패, 로컬 시도: {e}")
    _local_delete_timer_record(lecture_name, filename)
