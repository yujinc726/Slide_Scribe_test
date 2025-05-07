import os
import streamlit as st

def get_user_base_dir() -> str:
    """Return timer_logs/<user_id> directory path based on current session user id.
    If user_id not provided, defaults to 'anonymous'."""
    user_id = st.session_state.get('user_id', 'anonymous') or 'anonymous'
    return os.path.join('timer_logs', user_id) 