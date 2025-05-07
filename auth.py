import os
import json
import streamlit as st
from github_storage import github_enabled, load_global_json, save_global_json

_USERS_FILE = "users.json"  # stored at repo root when using GitHub or local disk otherwise


def _local_users_path() -> str:
    return os.path.join(_USERS_FILE)


def _read_local():
    if not os.path.exists(_local_users_path()):
        return {}
    try:
        with open(_local_users_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_local(data: dict):
    with open(_local_users_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_users():
    if github_enabled():
        data = load_global_json(_USERS_FILE)
        return data if isinstance(data, dict) else {}
    return _read_local()


def _save_users(data: dict):
    if github_enabled():
        return save_global_json(_USERS_FILE, data)
    _write_local(data)
    return True


def register_user(username: str, password: str) -> bool:
    users = _load_users()
    if username in users:
        return False
    users[username] = password
    return _save_users(users)


def validate_user(username: str, password: str) -> bool:
    users = _load_users()
    return users.get(username) == password


def list_users():
    return list(_load_users().keys()) 