import pandas as pd
import re
from datetime import datetime
import streamlit as st
import json
from browser_store import load_records, list_record_ids, load_lecture_names

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
    return load_lecture_names()

# LocalStorage 기반 기록 ID 조회
def get_record_ids_for_lecture(lecture_name):
    return list_record_ids(lecture_name)

def process_files(srt_file=None, records:list|None=None):
    """타이머 기록(list of dict)과 SRT 파일을 합쳐 슬라이드별 자막을 반환"""
    if records is None:
        st.error("타이머 기록이 필요합니다")
        return None
    df = pd.DataFrame(records)
    
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
                record_ids = get_record_ids_for_lecture(selected_lecture)
                if not record_ids:
                    st.info("타이머 기록이 없습니다.")
            else:
                record_ids = None
            if record_ids:
                selected_record_id = st.selectbox(
                    "기록 선택",
                    record_ids,
                    key="json_file_selector",
                    index=None,
                    placeholder="기록을 선택해주세요",
                    disabled=not selected_lecture
                )
                if selected_record_id:
                    selected_record_id_val = selected_record_id
                else:
                    selected_record_id_val = None
            else:
                selected_record_id_val = None
        else:
            st.info("등록된 강의가 없습니다.")
            selected_record_id_val = None
        
        # 처리 버튼
        if st.button("Parse SRT", type='primary', use_container_width=True, disabled=not (srt_file and selected_record_id_val)):
            if srt_file is None:
                st.error("SRT 파일을 업로드 해주세요.")
            elif selected_record_id_val is None:
                st.error("기록을 선택해주세요.")
            else:
                with st.spinner("Processing..."):
                    records = load_records(selected_lecture, selected_record_id_val)
                    # JSON 비슷한 구조로 df 변환
                    df_records = pd.DataFrame(records)
                    st.session_state.result_df = process_files(srt_file, records)
    
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
            st.info("SRT 파일을 업로드하고, 기록을 선택해주세요.")