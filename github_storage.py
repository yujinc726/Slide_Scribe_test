import json
import base64
from datetime import datetime
import streamlit as st

from github import Github


# --- Simple manual cache --------------------------------------------------
# lru_cache 는 *실패한* 호출 결과(None)도 캐시해 버리기 때문에, 첫 호출 시 토큰이
# 설정되지 않았거나 일시적인 오류가 나면 세션 내내 GitHub 를 사용할 수 없게 된다.
#
# 아래 방식은 "성공한 경우"에만 캐싱하므로 이런 문제를 피할 수 있다.

_REPO_CACHE = None  # type: ignore


def _get_repo():
    """Return PyGithub Repository object, caching it after first success.

    • 성공적으로 Repo 객체를 가져온 뒤에만 캐시한다.
    • 첫 호출이 실패했더라도, 이후 토큰이 설정되면 재시도 가능하다.
    """

    global _REPO_CACHE

    # 이미 성공적으로 받아온 Repo 가 있으면 그대로 사용
    if _REPO_CACHE is not None:
        return _REPO_CACHE

    token = st.secrets.get("GITHUB_TOKEN") if hasattr(st, "secrets") else None
    repo_name = st.secrets.get("GITHUB_REPO") if hasattr(st, "secrets") else None

    if not token or not repo_name or Github is None:
        return None

    try:
        gh = Github(token)
        _REPO_CACHE = gh.get_repo(repo_name)
        return _REPO_CACHE
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