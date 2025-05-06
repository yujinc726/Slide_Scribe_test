import streamlit as st
import boto3
from botocore.exceptions import ClientError
from slide_timer import lecture_timer_tab
from srt_parser import srt_parser_tab
from settings import settings_tab
import json
import os
import uuid

# Streamlit page configuration
st.set_page_config(
    page_title="Slide Scribe",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
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

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'SlideScribeUsers'
table = dynamodb.Table(table_name)

# Helper functions for user authentication
def create_user(user_id, password):
    try:
        table.put_item(
            Item={
                'user_id': user_id,
                'password': password
            },
            ConditionExpression='attribute_not_exists(user_id)'
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            st.error("User ID already exists!")
        else:
            st.error(f"Error creating user: {e}")
        return False

def authenticate_user(user_id, password):
    try:
        response = table.get_item(Key={'user_id': user_id})
        if 'Item' in response and response['Item']['password'] == password:
            return True
        return False
    except ClientError as e:
        st.error(f"Error authenticating user: {e}")
        return False

def get_json_storage_path(user_id=None):
    if user_id:  # Logged-in user
        user_folder = f"data/{user_id}"
        os.makedirs(user_folder, exist_ok=True)
        return user_folder
    else:  # Non-member
        return None  # JSON will be stored in session_state

def save_json_data(data, filename, user_id=None):
    if user_id:
        storage_path = get_json_storage_path(user_id)
        file_path = os.path.join(storage_path, filename)
        with open(file_path, 'w') as f:
            json.dump(data, f)
    else:
        # Store in session_state for non-members
        if 'non_member_data' not in st.session_state:
            st.session_state.non_member_data = {}
        st.session_state.non_member_data[filename] = data

def load_json_data(filename, user_id=None):
    if user_id:
        storage_path = get_json_storage_path(user_id)
        file_path = os.path.join(storage_path, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None
    else:
        return st.session_state.non_member_data.get(filename) if 'non_member_data' in st.session_state else None

def login_signup_page():
    st.title("Slide Scribe - Login / Signup")
    st.markdown("Made by 차유진")

    # Initialize session state for login
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Tabs for Login, Signup, Non-member access
    login_tab, signup_tab, non_member_tab = st.tabs(["Login", "Signup", "Non-Member"])

    with login_tab:
        st.subheader("Login")
        user_id = st.text_input("User ID", key="login_user_id")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if authenticate_user(user_id, password):
                st.session_state.user_id = user_id
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid User ID or Password")

    with signup_tab:
        st.subheader("Signup")
        new_user_id = st.text_input("New User ID", key="signup_user_id")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        if st.button("Signup"):
            if new_password == confirm_password:
                if create_user(new_user_id, new_password):
                    st.success("User created successfully! Please login.")
            else:
                st.error("Passwords do not match!")

    with non_member_tab:
        st.subheader("Non-Member Access")
        if st.button("Continue as Non-Member"):
            st.session_state.user_id = None
            st.session_state.logged_in = True
            st.success("Continuing as non-member")
            st.rerun()

def main():
    try:
        # Check if user is logged in
        if 'logged_in' not in st.session_state or not st.session_state.logged_in:
            login_signup_page()
            return

        # Initialize session state
        if 'result_df' not in st.session_state:
            st.session_state.result_df = None
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "SRT Parser"

        st.title("Slide Scribe")
        st.markdown(f"Made by 차유진 | Logged in as: {st.session_state.user_id or 'Non-Member'}")

        # Logout button
        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.logged_in = False
            st.session_state.non_member_data = {}
            st.rerun()

        # Tabs for main app
        tab1, tab2, tab3 = st.tabs(["⏱️ Slide Timer", "📜 SRT Parser", "⚙️ Settings"])

        with tab1:
            lecture_timer_tab()
        
        with tab2:
            srt_parser_tab()
            
        with tab3:
            settings_tab()

    except Exception as e:
        st.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()