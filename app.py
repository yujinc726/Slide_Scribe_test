import streamlit as st
from slide_timer import lecture_timer_tab
from srt_parser import srt_parser_tab
from settings import settings_tab
from auth_storage import authenticate_user

st.set_page_config(
    page_title="Slide Scribe",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def main():
    try:
        # Check if user is authenticated
        if authenticate_user():
            # 세션 상태 초기화
            if 'result_df' not in st.session_state:
                st.session_state.result_df = None
            if 'active_tab' not in st.session_state:
                st.session_state.active_tab = "SRT Parser"
            st.title('Slide Scribe')
            st.markdown('Made by 차유진')
            # 탭 생성
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