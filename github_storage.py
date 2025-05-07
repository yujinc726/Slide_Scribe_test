import json
import base64
import os
from datetime import datetime
import streamlit as st

try:
    from github import Github
except ImportError:
    Github = None  # PyGithub 미설치 시 우회


def _get_repo():
    """Return PyGithub Repository object.

    Priority of credential sources:
    1. Streamlit Cloud secrets (``st.secrets``)
    2. Environment variables (``GITHUB_TOKEN`` / ``GITHUB_REPO``)

    If credentials (or the *PyGithub* package) are missing, or if the repository
    cannot be accessed, ``None`` is returned so that callers can gracefully
    fall back to local storage.
    """

    # --- fetch credentials from Streamlit secrets when available ---
    token = None
    repo_name = None
    if hasattr(st, "secrets"):
        try:
            token = st.secrets.get("GITHUB_TOKEN")
            repo_name = st.secrets.get("GITHUB_REPO")
        except Exception:
            # If st.secrets behaves like a mapping but raises errors upon access
            # we simply ignore and fall back to environment variables.
            pass

    # --- environment variable fallback (useful for local execution) ---
    token = token or os.getenv("GITHUB_TOKEN")
    repo_name = repo_name or os.getenv("GITHUB_REPO")

    # Ensure PyGithub is available and we have the required credentials.
    if not token or not repo_name or Github is None:
        return None

    # Try to obtain the repository instance. Any exception here most likely
    # indicates invalid credentials or a typo in the repository name.
    try:
        gh = Github(token)
        return gh.get_repo(repo_name)
    except Exception:
        # For debugging purposes in a Streamlit app, emit a warning; swallow any
        # errors if Streamlit is not initialised (e.g. during unit tests).
        try:
            st.warning("GitHub access failed – falling back to local storage.")
        except Exception:
            pass
        return None


def github_enabled() -> bool:
    return _get_repo() is not None


def _user_base_dir(user_id: str) -> str:
    return f"timer_logs/{user_id}"


def list_lectures(user_id: str):
    repo = _get_repo()
    if repo is None:
        return []
    base = _user_base_dir(user_id)
    try:
        contents = repo.get_contents(base)
        return [c.name for c in contents if c.type == "dir"]
    except Exception:
        return []


def list_json(user_id: str, lecture: str):
    repo = _get_repo()
    if repo is None:
        return []
    path = f"{_user_base_dir(user_id)}/{lecture}"
    try:
        contents = repo.get_contents(path)
        return [c.name for c in contents if c.name.endswith(".json")]
    except Exception:
        return []


def load_json(user_id: str, lecture: str, filename: str):
    repo = _get_repo()
    if repo is None:
        return []
    path = f"{_user_base_dir(user_id)}/{lecture}/{filename}"
    try:
        file_content = repo.get_contents(path)
        raw = base64.b64decode(file_content.content).decode()
        return json.loads(raw)
    except Exception:
        return []


def save_json(user_id: str, lecture: str, filename: str, data):
    """Create or update a JSON file in GitHub."""
    repo = _get_repo()
    if repo is None:
        return False
    path = f"{_user_base_dir(user_id)}/{lecture}/{filename}"
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    message = f"{lecture}/{filename} updated {datetime.utcnow().isoformat()}"
    try:
        existing = repo.get_contents(path)
        repo.update_file(path, message, raw, existing.sha)
    except Exception:
        # create new file (or directory missing)
        try:
            repo.create_file(path, message, raw)
        except Exception:
            return False
    return True


# -------- global file helpers --------


def load_global_json(filename: str):
    repo = _get_repo()
    if repo is None:
        return None
    try:
        file_content = repo.get_contents(filename)
        raw = base64.b64decode(file_content.content).decode()
        return json.loads(raw)
    except Exception:
        return None


def save_global_json(filename: str, data):
    repo = _get_repo()
    if repo is None:
        return False
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    message = f"{filename} updated {datetime.utcnow().isoformat()}"
    try:
        existing = repo.get_contents(filename)
        repo.update_file(filename, message, raw, existing.sha)
    except Exception:
        try:
            repo.create_file(filename, message, raw)
        except Exception:
            return False
    return True 