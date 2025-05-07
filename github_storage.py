import json
import base64
from datetime import datetime
import streamlit as st

try:
    from github import Github
except ImportError:
    Github = None  # PyGithub 미설치 시 우회


def _get_repo():
    """return PyGithub Repository object using secrets, or None if unavailable"""
    token = st.secrets.get("GITHUB_TOKEN") if hasattr(st, "secrets") else None
    repo_name = st.secrets.get("GITHUB_REPO") if hasattr(st, "secrets") else None
    if not token or not repo_name or Github is None:
        return None
    try:
        gh = Github(token)
        return gh.get_repo(repo_name)
    except Exception:
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