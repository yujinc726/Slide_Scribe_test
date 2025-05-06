import streamlit as st
import boto3
from s3_utils import save_json_to_s3, load_json_from_s3
from auth import login_page
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

# Custom CSS with shorter input fields
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
            
        # Save JSON data on tab interaction
        if st.session_state.is_authenticated and st.session_state.user_id:
            try:
                save_json_to_s3(st.session_state.user_id, st.session_state.json_data, 'data.json')
            except Exception as e:
                st.error(f"Error saving JSON data to S3: {e}")
        
    except Exception as e:
        st.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()