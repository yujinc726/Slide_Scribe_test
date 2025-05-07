import streamlit as st
from slide_timer import lecture_timer_tab
from srt_parser import srt_parser_tab
from settings import settings_tab
from auth import validate_user, register_user

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
        min-height: 200px !important;  /* 최소 높이 설정 */
        max-height: 400px !important;  /* 최대 높이 설정, 스크롤 가능 */
        overflow-y: auto !important;    /* 세로 스크롤 활성화 */
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 16px !important;
        line-height: 2.0 !important;
        padding: 15px !important;
        border-radius: 5px !important;
        margin-bottom: 20px !important;
        white-space: pre-wrap !important;  /* 줄바꿈 활성화 */
        word-wrap: break-word !important;  /* 단어 단위 줄바꿈 */
        overflow-wrap: break-word !important;  /* 긴 단어 줄바꿈 */
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title('Slide Scribe')
    st.markdown('Made by 차유진')
    try:
        # 로그인 상태 관리
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None

        def login_form():
            with st.form("login_form"):
                st.subheader("Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
            if submitted:
                if validate_user(username, password):
                    st.session_state.user_id = username
                    st.success("Login successful!")
                else:
                    st.error("Invalid credentials")

        def register_form():
            with st.form("register_form"):
                st.subheader("Register")
                username = st.text_input("Username", key="reg_user")
                password = st.text_input("Password", type="password", key="reg_pass")
                password2 = st.text_input("Confirm Password", type="password", key="reg_pass2")
                submitted = st.form_submit_button("Register")
            if submitted:
                if password != password2:
                    st.error("Passwords do not match.")
                elif register_user(username, password):
                    st.success("Registration successful. Please log in.")
                else:
                    st.error("Username already exists.")

        if st.session_state.user_id is None:
            auth_tab = st.tabs(["로그인", "회원가입"])
            if auth_tab == "로그인":
                login_form()
            else:
                register_form()
            return
        
        # 세션 상태 초기화
        if 'result_df' not in st.session_state:
            st.session_state.result_df = None
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "SRT Parser"
        # st.title('Slide Scribe')
        # st.markdown('Made by 차유진')
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