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

    js_code = """
(function () {
    let uid = window.localStorage.getItem('slideScribe_user_id');
    if (!uid) {
        if (window.crypto && window.crypto.randomUUID) {
            uid = window.crypto.randomUUID();
        } else {
            // Very old browsers – generate a naive UUID
            const s4 = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
            uid = s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
        }
        window.localStorage.setItem('slideScribe_user_id', uid);
    }
    return uid;
})()
"""
    user_id = streamlit_js_eval(js_expressions=js_code, want_output=True, key="__get_user_id")
    # If the component failed to return a value we generate one server-side.
    return user_id or str(uuid.uuid4())


def get_user_id() -> str:
    """Return a cached unique id for the current browser session."""
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = _obtain_user_id_from_browser()
    return st.session_state['user_id']


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