import pandas as pd
import re
from datetime import datetime
import streamlit as st
import json
import os
from utils import get_user_base_dir

def parse_srt_time(time_str):
    """SRT 및 CSV 시간 문자열을 초 단위로 변환"""
    time_str = time_str.replace('.', ',')
    try:
        time_obj = datetime.strptime(time_str, "%H:%M:%S,%f")
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1e6
    except ValueError as e:
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM:SS,fff") from e

def read_srt_file(srt_content):
    """SRT 파일 내용을 읽고 자막 데이터를 파싱"""
    subtitles = []
    blocks = srt_content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        index = lines[0]
        time_range = lines[1]
        text = ' '.join(lines[2:]).replace('\n', ' ')
        
        try:
            start_time, end_time = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", time_range).groups()
            subtitles.append({
                'index': index,
                'start_time': parse_srt_time(start_time),
                'end_time': parse_srt_time(end_time),
                'text': text
            })
        except (re.error, ValueError):
            continue
    
    return subtitles

def get_available_lectures():
    """lectures 디렉토리에서 사용 가능한 강의 목록 가져오기"""
    timer_logs_dir = get_user_base_dir()
    lectures = []
    
    if os.path.exists(timer_logs_dir):
        for lecture_name in os.listdir(timer_logs_dir):
            lecture_path = os.path.join(timer_logs_dir, lecture_name)
            if os.path.isdir(lecture_path):
                lectures.append(lecture_name)
    
    return lectures

def get_json_files_for_lecture(lecture_name):
    """특정 강의 디렉토리에서 사용 가능한 JSON 파일 목록 가져오기"""
    timer_logs_dir = os.path.join(get_user_base_dir(), lecture_name)
    json_files = []
    
    if os.path.exists(timer_logs_dir):
        for file_name in os.listdir(timer_logs_dir):
            if file_name.endswith('.json'):
                json_files.append(file_name)
    
    return json_files

def load_json_file(json_path):
    """JSON 파일에서 타이머 기록 로드"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"JSON 파일 로드 중 오류: {e}")
        return []

def process_files(srt_file=None, json_path=None):
    """JSON과 SRT 파일을 처리하여 슬라이드별로 자막을 합쳐 데이터프레임 반환"""
    # 타이머 기록 읽기 (JSON 파일)
    if json_path:
        records = load_json_file(json_path)
        df = pd.DataFrame(records)
    else:
        st.error("타이머 기록(JSON) 필요")
        return None
    
    # SRT 파일 읽기 (Streamlit UploadedFile 처리)
    srt_content = srt_file.read().decode('utf-8')
    subtitles = read_srt_file(srt_content)
    
    # 출력 데이터 준비
    output_data = []
    
    # 각 슬라이드별로 자막 매핑
    for _, row in df.iterrows():
        slide_num = row['slide_number'] if 'slide_number' in df.columns else row['Slide Number']
        start_time = parse_srt_time(row['start_time'] if 'start_time' in df.columns else row['Start Time'])
        end_time = parse_srt_time(row['end_time'] if 'end_time' in df.columns else row['End Time'])
        
        # 해당 시간 구간에 속하는 자막 텍스트 수집
        slide_texts = []
        for subtitle in subtitles:
            if subtitle['start_time'] >= start_time and subtitle['end_time'] <= end_time:
                slide_texts.append(subtitle['text'])
        
        # 자막 텍스트를 공백으로 합침
        combined_text = ' '.join(slide_texts)
        
        if combined_text:  # 텍스트가 있는 경우에만 추가
            output_data.append({
                'Slide Number': slide_num,
                'Text': combined_text
            })
    
    # 데이터프레임 반환
    if output_data:
        return pd.DataFrame(output_data)
    else:
        return None

def srt_parser_tab():
    """SRT Parser 탭 구현"""
    # 초기화
    if 'result_df' not in st.session_state:
        st.session_state.result_df = None
    
    # 레이아웃 설정
    col1, col2 = st.columns([1, 2])  # 좌측: 파일 업로드, 우측: 결과
    
    with col1:
        # st.subheader("File Upload")
        # SRT 파일 업로드
        srt_file = st.file_uploader("SRT 파일 업로드", type=["srt"], key="srt_uploader")
        
        # 강의 선택 및 JSON 파일 선택
        available_lectures = get_available_lectures()
        if available_lectures:
            selected_lecture = st.selectbox(
                "강의 선택",
                available_lectures,
                key="lecture_selector",
                index=None,
                placeholder="강의를 선택해주세요"
            )
            
            if selected_lecture:
                json_files = get_json_files_for_lecture(selected_lecture)
                if not json_files:
                    st.info("타이머 기록이 없습니다.")
            else:
                json_files = None
            if json_files:
                selected_json_file = st.selectbox(
                    "기록 선택",
                    json_files,
                    key="json_file_selector",
                    index=None,
                    placeholder="기록을 선택해주세요",
                    disabled=not selected_lecture
                )
                if selected_json_file:
                    json_path = os.path.join(get_user_base_dir(), selected_lecture, selected_json_file)
            else:
                json_path = None
        else:
            st.info("등록된 강의가 없습니다.")
            json_path = None
        
        # 처리 버튼
        if st.button("Parse SRT", type='primary', use_container_width=True, disabled=not (srt_file and json_path)):
            if srt_file is None:
                st.error("SRT 파일을 업로드 해주세요.")
            elif json_path is None:
                st.error("JSON 파일을 선택해주세요.")
            else:
                with st.spinner("Processing..."):
                    st.session_state.result_df = process_files(srt_file, json_path)
    
    with col2:
        st.subheader("Parsed SRT")
        if st.session_state.result_df is not None:
            if not st.session_state.result_df.empty:
                for _, row in st.session_state.result_df.iterrows():
                    st.markdown(f'<div class="slide-number">Slide {row["Slide Number"]}</div>', unsafe_allow_html=True)
                    # 마크다운 코드 블록으로 텍스트 출력 (문자열 분리)
                    text_content = row['Text']
                    markdown_text = f"```text\n{text_content}\n```"
                    st.markdown(markdown_text)
            else:
                st.warning("추출된 내용이 없습니다.")
        else:
            st.info("SRT 파일을 업로드하고, JSON 파일을 선택해주세요.")