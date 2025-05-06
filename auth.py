import streamlit as st
import boto3
import json
from s3_utils import save_json_to_s3, load_json_from_s3

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=st.secrets.get("AWS_SECRET_ACCESS_KEY"),
    region_name=st.secrets.get("AWS_DEFAULT_REGION")
)
BUCKET_NAME = "slide-scribe-data"

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
    st.title("Slide Scribe")
    
    # Tabs for Login and Signup
    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])
    
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
                    st.session_state.json_data = load_json_from_s3(user_id, 'data.json')
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