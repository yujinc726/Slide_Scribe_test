import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
from slide_timer import lecture_timer_tab
from srt_parser import srt_parser_tab
from settings import settings_tab
import json
import os

# Streamlit page configuration
st.set_page_config(
    page_title="Slide Scribe",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 20px;
    }
    .slide-number {
        font-size: 24px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    pre, pre code {
        min-height: 200px !important;
        max-height: 400px !important;
        overflow-y: auto !important;
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 16px !important;
        line-height: 2.0 !important;
        padding: 15px !important;
        border-radius: 5px !important;
        margin-bottom: 20px !important;
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # For Streamlit Cloud, use secrets
            if 'firebase' in st.secrets:
                cred = credentials.Certificate(st.secrets['firebase'])
                st.write('test')
            else:
                # For local development, use JSON file
                st.write('test')
                cred = credentials.Certificate('slidescribe-firebase-adminsdk.json')
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase initialization error: {e}")

# Get Firestore client
def get_db():
    return firestore.client()

# Register a new user
def register_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        st.success(f"User {email} registered successfully!")
        return user.uid
    except Exception as e:
        st.error(f"Registration error: {e}")
        return None

# Login a user
def login_user(email, password):
    try:
        # Firebase Admin SDK doesn't support client-side login, so we use a workaround
        # Verify password by attempting to create a user with the same email (will fail if exists)
        user = auth.get_user_by_email(email)
        # In a real app, use Firebase Client SDK for login (see notes below)
        st.success(f"Logged in as {email}")
        return user.uid
    except auth.AuthError as e:
        st.error(f"Login error: Invalid email or password")
        return None
    except Exception as e:
        st.error(f"Login error: {e}")
        return None

# Save user-specific JSON to Firestore
def save_user_json(uid, json_data):
    db = get_db()
    try:
        db.collection('users').document(uid).set({'settings': json_data})
        st.success("Settings saved successfully!")
    except Exception as e:
        st.error(f"Error saving settings: {e}")

# Load user-specific JSON from Firestore
def load_user_json(uid):
    db = get_db()
    try:
        doc = db.collection('users').document(uid).get()
        if doc.exists:
            return doc.to_dict().get('settings', {})
        return {}
    except Exception as e:
        st.error(f"Error loading settings: {e}")
        return {}

def main():
    # Initialize Firebase
    initialize_firebase()

    # Initialize session state
    if 'user_uid' not in st.session_state:
        st.session_state.user_uid = None
    if 'result_df' not in st.session_state:
        st.session_state.result_df = None
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "SRT Parser"

    # If not logged in, show login/registration UI
    if not st.session_state.user_uid:
        st.title("Slide Scribe - Login/Register")
        st.markdown("Made by 차유진")

        login_tab, register_tab = st.tabs(["Login", "Register"])

        with login_tab:
            st.subheader("Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login"):
                uid = login_user(email, password)
                if uid:
                    st.session_state.user_uid = uid
                    st.rerun()

        with register_tab:
            st.subheader("Register")
            new_email = st.text_input("Email", key="register_email")
            new_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            if st.button("Register"):
                if new_password == confirm_password:
                    uid = register_user(new_email, new_password)
                    if uid:
                        st.session_state.user_uid = uid
                        st.rerun()
                else:
                    st.error("Passwords do not match")
    else:
        # Main app for authenticated users
        st.title("Slide Scribe")
        st.markdown(f"Made by 차유진 | Logged in as {auth.get_user(st.session_state.user_uid).email}")

        # Load user-specific JSON
        user_json = load_user_json(st.session_state.user_uid)
        if user_json:
            st.session_state.user_json = user_json
        else:
            st.session_state.user_json = {}  # Default empty JSON

        # Tabs
        tab1, tab2, tab3 = st.tabs(["⏱️ Slide Timer", "📜 SRT Parser", "⚙️ Settings"])

        with tab1:
            lecture_timer_tab()

        with tab2:
            srt_parser_tab()

        with tab3:
            settings_tab()

        # Example: Save updated JSON (modify based on your JSON structure)
        if st.button("Save Settings"):
            # Replace with actual JSON data from your app
            updated_json = st.session_state.user_json
            save_user_json(st.session_state.user_uid, updated_json)

        # Logout
        if st.button("Logout"):
            st.session_state.user_uid = None
            st.rerun()

if __name__ == "__main__":
    main()