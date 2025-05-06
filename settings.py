import streamlit as st
import json
import pandas as pd
import time

# Helpers backed by localStorage
from storage_utils import (
    load_lecture_names,
    save_lecture_names,
    get_existing_json_files,
    load_records_from_json,
    save_records_to_json,
    ls_set,
    ls_delete,
)

# `os` and `shutil` kept only for handling uploaded filenames etc.
import os
import shutil

def ensure_directory(_directory):
    return None

def get_json_files_for_lecture(lecture_name):
    mapping = {os.path.basename(k): k for k in get_existing_json_files(lecture_name)}
    return mapping

def load_json_file(storage_key):
    return load_records_from_json(storage_key)

def save_json_file(storage_key, data):
    try:
        ls_set(storage_key, data)
        return True
    except Exception as e:
        st.error(f"JSON 저장 오류: {e}")
        return False

def manage_json_files():
    """JSON 파일 관리 기능 구현"""
    st.subheader("JSON 파일 관리")
    
    # 강의 선택
    available_lectures = load_lecture_names()
    if not available_lectures:
        st.info("등록된 강의가 없습니다.")
        return
    
    selected_lecture = st.selectbox(
        "강의 선택",
        available_lectures,
        key="lecture_selector_json",
        index=None,
        placeholder='강의를 선택해주세요'
    )
    
    if selected_lecture:
        with st.expander("로컬에서 기록 불러오기"):
            # 파일 업로더 키 초기화
            if f"uploader_key_{selected_lecture}" not in st.session_state:
                st.session_state[f"uploader_key_{selected_lecture}"] = 0
            
            # JSON 파일 업로드
            uploaded_file = st.file_uploader(
                "JSON 파일을 선택하세요",
                type=["json"],
                key=f"json_uploader_{selected_lecture}_{st.session_state[f'uploader_key_{selected_lecture}']}"
            )
            
            # 업로드된 파일을 세션 상태에 저장
            if uploaded_file is not None:
                st.session_state[f"uploaded_file_{selected_lecture}"] = {
                    "name": uploaded_file.name,
                    "content": uploaded_file.read()
                }
            else:
                # 파일 업로더가 비어 있으면 세션 상태 초기화
                st.session_state.pop(f"uploaded_file_{selected_lecture}", None)
            
            # 업로드된 기록 저장 버튼
            if st.button(
                "로컬 기록 불러오기",
                key=f"save_uploaded_file_{selected_lecture}",
                disabled=not st.session_state.get(f"uploaded_file_{selected_lecture}")
            ):
                uploaded_file_info = st.session_state[f"uploaded_file_{selected_lecture}"]
                try:
                    # JSON 파일 검증
                    json_data = json.loads(uploaded_file_info["content"])
                    upload_key = f"timer_logs/{selected_lecture}/{uploaded_file_info['name']}"
                    ls_set(upload_key, json_data)
                    # 성공 메시지 저장
                    st.session_state[f"upload_success_{selected_lecture}"] = f"{uploaded_file_info['name']} 파일을 불러왔습니다."
                    # 업로드 상태 초기화 및 파일 업로더 리셋
                    st.session_state.pop(f"uploaded_file_{selected_lecture}", None)
                    st.session_state[f"uploader_key_{selected_lecture}"] += 1
                except json.JSONDecodeError:
                    st.error("업로드된 파일이 유효한 JSON 형식이 아닙니다.")
                except Exception as e:
                    st.error(f"파일 저장 중 오류: {e}")
            
            # 성공 메시지 표시
            if st.session_state.get(f"upload_success_{selected_lecture}"):
                st.success(st.session_state[f"upload_success_{selected_lecture}"])
                # 메시지 표시 후 지연해서 제거
                time.sleep(2)
                st.session_state.pop(f"upload_success_{selected_lecture}", None)
        
        with st.expander("JSON 파일 관리"):
            # JSON 파일 목록
            mapping = get_json_files_for_lecture(selected_lecture)
            json_files = list(mapping.keys())
            selected_json = st.selectbox(
                "JSON 파일 선택",
                json_files,
                key="json_selector",
                index=None,
                placeholder="JSON 파일을 선택해주세요"
            )
            
            if selected_json:
                # 파일 삭제와 다운로드 버튼 (JSON 파일 선택 바로 아래)
                col1, col2 = st.columns(2)
                with col1:
                    # JSON 파일 다운로드 (from browser storage)
                    storage_key = mapping[selected_json]
                    file_content = json.dumps(load_json_file(storage_key), ensure_ascii=False, indent=2)
                    st.download_button(
                        label="기록 다운로드",
                        data=file_content,
                        file_name=selected_json,
                        mime="application/json",
                        use_container_width=True,
                        disabled=not selected_json
                    )
                with col2:
                    if st.button("기록 삭제", use_container_width=True, disabled=not selected_json):
                        try:
                            ls_delete(storage_key)
                            st.success(f"{selected_json} 기록이 삭제되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 중 오류: {e}")
                
                # 파일 내용 불러오기
                json_data = load_json_file(storage_key)
                
                if not json_data:
                    st.warning("선택한 파일을 불러올 수 없거나 파일이 비어있습니다.")
                    return
                
                # 데이터프레임으로 변환
                df = pd.DataFrame(json_data)
                
                # 데이터 에디터
                st.write("기록 편집")
                edited_df = st.data_editor(
                    df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"json_editor_{selected_lecture}_{selected_json}",
                    column_config={
                        "slide_number": st.column_config.TextColumn("Slide Number", help="슬라이드 번호"),
                        "start_time": st.column_config.TextColumn("Start Time", help="시작 시간"),
                        "end_time": st.column_config.TextColumn("End Time", help="종료 시간"),
                        "notes": st.column_config.TextColumn("Notes", help="메모")
                    }
                )
                
                # 변경사항 저장 버튼 (데이터 에디터 아래)
                if st.button("변경사항 저장", use_container_width=True):
                    if save_json_file(storage_key, edited_df.to_dict('records')):
                        st.success(f"{selected_json} 파일이 저장되었습니다.")
                    else:
                        st.error("파일 저장 중 오류가 발생했습니다.")

def manage_lectures():
    """강의 이름 관리 기능 구현"""
    st.subheader("강의 목록 관리")
    
    with st.expander("강의 추가"):
        new_lecture = st.text_input("강의 추가", key="new_lecture_input_settings", placeholder="강의명 입력", label_visibility="collapsed")
        if st.button("강의 추가", key="add_lecture_settings"):
            if new_lecture.strip():
                if new_lecture not in st.session_state.lecture_names:
                    st.session_state.lecture_names.append(new_lecture)
                    save_lecture_names(st.session_state.lecture_names)
                    # 디렉토리 생성
                    ensure_directory(f"timer_logs/{new_lecture}")
                    st.rerun()
                    st.success(f"강의가 추가되었습니다: {new_lecture}")
                else:
                    st.warning("이미 존재하는 강의 이름입니다.")
            else:
                st.warning("강의 이름을 입력해주세요.")
        # 초기화
        if 'lecture_names' not in st.session_state:
            st.session_state.lecture_names = load_lecture_names()
    
    with st.expander("강의 삭제"):
        if st.session_state.lecture_names:
            selected_lectures = st.multiselect(
                "강의 삭제",
                st.session_state.lecture_names,
                default=[],
                key="lecture_list_settings",
                placeholder="삭제할 강의 선택",
                label_visibility="collapsed"
            )
        else:
            st.info("등록된 강의가 없습니다.")
            selected_lectures = []
        if st.button("강의 삭제", key="remove_lectures_settings"):
            if selected_lectures:
                for lecture in selected_lectures:
                    # remove all associated storage keys
                    for key in get_existing_json_files(lecture):
                        ls_delete(key)
                    st.session_state.lecture_names.remove(lecture)
                save_lecture_names(st.session_state.lecture_names)
                st.success(f"{len(selected_lectures)}개의 강의가 삭제되었습니다.")
                st.rerun()
            else:
                st.warning("삭제할 강의를 선택해주세요.")

def settings_tab():
    """Settings 탭 구현"""
    with st.container():
        manage_lectures()
    st.divider()
    with st.container():
        manage_json_files()