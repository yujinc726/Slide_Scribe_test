import streamlit as st
import uuid
import os

# We use a small JS snippet (via streamlit_js_eval) to persist a random UUID in the
# browser's localStorage. This value is unique per visitor and survives page
# refreshes while remaining completely client-side so that each visitor gets a
# private workspace on the Streamlit Cloud backend.
try:
    from streamlit_js_eval import streamlit_js_eval  # type: ignore
except ModuleNotFoundError:
    # The package will be added to requirements.txt.  Fallback for local runs so
    # that the rest of the code does not break while the dependency is missing.
    streamlit_js_eval = None  # type: ignore


def _obtain_user_id_from_browser() -> str:
    """Return a stable UUID stored in the client's browser localStorage.

    When the application is loaded, we run a small JavaScript snippet that:
    1. Tries to read an existing value under the key `slideScribe_user_id` from
       `window.localStorage`.
    2. If absent, generates a brand-new `crypto.randomUUID()` and stores it.
    3. Returns the value back to Python where we cache it in `st.session_state`.

    If the JS bridge is not available (e.g. when running in a headless context
    or during unit tests) we fall back to creating a random UUID on the Python
    side so that the code path still works.
    """
    if streamlit_js_eval is None:
        # Fallback – will generate a new value on every run.  Acceptable for
        # local/scripts but not for real users.
        return str(uuid.uuid4())

    # Step 1: try to read existing value without creating a new one
    get_code = "return window.localStorage.getItem('slideScribe_user_id');"
    stored = streamlit_js_eval(js_expressions=get_code, want_output=True, key="__get_uid")

    if stored:
        return stored

    # Step 2: not found => create on Python side for authoritative value
    new_uid = str(uuid.uuid4())

    # Persist it to browser localStorage (fire-and-forget)
    set_code = f"window.localStorage.setItem('slideScribe_user_id', '{new_uid}');"
    try:
        streamlit_js_eval(js_expressions=set_code, want_output=False, key="__set_uid")
    except Exception:
        # Even if JS bridge fails we still return the python-side uid.
        pass

    return new_uid


def get_user_id() -> str:
    """Return a cached unique id for the current browser session.

    If the stored value is missing or invalid (None, empty, not a string), we
    regenerate it to avoid propagation of bad state across reruns.
    """
    uid = st.session_state.get('user_id') if 'user_id' in st.session_state else None
    if not isinstance(uid, str) or not uid:
        uid = _obtain_user_id_from_browser()
        st.session_state['user_id'] = uid
    return uid


def user_timer_logs_dir() -> str:
    """Return (and create if necessary) the per-user directory for JSON logs."""
    directory = os.path.join("timer_logs", get_user_id())
    # Lazily create the directory so other code can rely on its existence.
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception:
        # On read-only or test environments we silently ignore failures – the
        # caller will deal with absence when attempting to write files.
        pass
    return directory 