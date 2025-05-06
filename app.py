import streamlit as st
import boto3
import json
import os
from slide_timer import lecture_timer_tab
from srt_parser import srt_parser_tab
from settings import settings_tab

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
    .login-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        max-width: 400px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=st.secrets.get("AWS_SECRET_ACCESS_KEY"),
    region_name=st.secrets.get("AWS_DEFAULT_REGION")
)
BUCKET_NAME = "slide-scribe-data"

def initialize_session_state():
    """Initialize session state variables."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    if 'json_data' not in st.session_state:
        st.session_state.json_data = {}
    if 'result_df' not in st.session_state:
        st.session_state.result_df = None
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "SRT Parser"

def save_json_to_s3(user_id, json_data):
    """Save JSON data to S3 under user_id folder."""
    try:
        file_path = f"{user_id}/data.json"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_path,
            Body=json.dumps(json_data, ensure_ascii=False).encode('utf-8')
        )
    except Exception as e:
        st.error(f"Error saving to S3: {e}")

def load_json_from_s3(user_id):
    """Load JSON data from S3 for a user."""
    try:
        file_path = f"{user_id}/data.json"
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_path)
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        return {}
    except Exception as e:
        st.error(f"Error loading from S3: {e}")
        return {}

def save_credentials(user_id, password):
    """Save user credentials to S3."""
    credentials = load_credentials()
    credentials[user_id] = password
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key="credentials.json",
            Body=json.dumps(credentials, ensure_ascii=False).encode('utf-8')
        )
    except Exception as e:
        st.error(f"Error saving credentials: {e}")

def load_credentials():
    """Load all credentials from S3."""
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key="credentials.json")
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        return {}
    except Exception as e:
        st.error(f"Error loading credentials: {e}")
        return {}

def login_page():
    """Render login and signup interface."""
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.subheader("Login or Sign Up")
    
    # Tabs for Login and Signup
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
    
    with login_tab:
        user_id = st.text_input("User ID", key="login_user_id")
        password = st.text_input("Password", type="password", key="login_password")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Login"):
                credentials = load_credentials()
                if user_id in credentials and credentials[user_id] == password:
                    st.session_state.user_id = user_id
                    st.session_state.is_authenticated = True
                    st.session_state.json_data = load_json_from_s3(user_id)
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        with col2:
            if st.button("Guest Login"):
                st.session_state.user_id = "guest"
                st.session_state.is_authenticated = False
                st.session_state.json_data = {}
                st.success("Logged in as guest")
                st.rerun()
    
    with signup_tab:
        new_user_id = st.text_input("New User ID", key="signup_user_id")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        if st.button("Sign Up"):
            credentials = load_credentials()
            if new_user_id in credentials:
                st.error("User ID already exists")
            elif new_user_id and new_password:
                save_credentials(new_user_id, new_password)
                st.success("Signed up successfully! Please log in.")
            else:
                st.error("Please fill in all fields")
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    try:
        initialize_session_state()
        
        # Show login page if not authenticated
        if not st.session_state.is_authenticated and st.session_state.user_id != "guest":
            login_page()
            return
        
        # Main app interface
        st.title('Slide Scribe')
        st.markdown('Made by 차유진')
        
        # Logout button
        col1, col2 = st.columns([9, 1])
        with col2:
            if st.session_state.is_authenticated or st.session_state.user_id == "guest":
                if st.button("Logout"):
                    st.session_state.user_id = None
                    st.session_state.is_authenticated = False
                    st.session_state.json_data = {}
                    st.rerun()
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["⏱️ Slide Timer", "📜 SRT Parser", "⚙️ Settings"])
        
        with tab1:
            lecture_timer_tab()
        
        with tab2:
            srt_parser_tab()
            
        with tab3:
            settings_tab()
            
        # Save JSON data on tab interaction (example)
        if st.session_state.is_authenticated:
            save_json_to_s3(st.session_state.user_id, st.session_state.json_data)
        
    except Exception as e:
        st.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()