import streamlit as st
from datetime import datetime, timedelta
import json
import pandas as pd
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript

def load_lecture_names():
    """Load lecture names from localStorage"""
    js_code = """
    return JSON.parse(localStorage.getItem('lecture_names') || '[]');
    """
    return st_javascript(js_code) or []

def save_lecture_names(lecture_names):
    """Save lecture names to localStorage"""
    js_code = f"""
    localStorage.setItem('lecture_names', JSON.stringify({json.dumps(lecture_names)}));
    return true;
    """
    st_javascript(js_code)

def save_records(lecture_name, records):
    """Save timer records to localStorage"""
    date = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M%S")
    file_name = f"{date}_{timestamp}.json"
    js_code = f"""
    const key = `records_{lecture_name}_{file_name}`;
    localStorage.setItem(key, JSON.stringify({json.dumps(records)}));
    return `{file_name}`;
    """
    return st_javascript(js_code)

def load_records(lecture_name, file_name):
    """Load records from localStorage"""
    js_code = f"""
    const key = `records_{lecture_name}_{file_name}`;
    return JSON.parse(localStorage.getItem(key) || '[]');
    """
    return st_javascript(js_code) or []

def get_existing_json_files(lecture_name):
    """Get list of JSON files for a lecture from localStorage"""
    js_code = f"""
    const files = [];
    for (let i = 0; i < localStorage.length; i++) {{
        const key = localStorage.key(i);
        if (key.startsWith(`records_{lecture_name}_`)) {{
            files.push(key.replace(`records_{lecture_name}_`, ''));
        }}
    }}
    return files;
    """
    return st_javascript(js_code) or []

def lecture_timer_tab():
    """Slide Timer 탭 구현"""
    # 세션 상태 초기화
    if 'lecture_names' not in st.session_state:
        st.session_state.lecture_names = load_lecture_names()
    if 'timer_running' not in st.session_state:
        st.session_state.timer_running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'timer_start' not in st.session_state:
        st.session_state.timer_start = None
    if 'elapsed_time' not in st.session_state:
        st.session_state.elapsed_time = 0
    if 'last_slide_start_time' not in st.session_state:
        st.session_state.last_slide_start_time = None
    if 'records' not in st.session_state:
        st.session_state.records = []
    if 'slide_number' not in st.session_state:
        st.session_state.slide_number = 1
    if 'start_time_value' not in st.session_state:
        st.session_state.start_time_value = "00:00:00.000"
    if 'notes_input' not in st.session_state:
        st.session_state.notes_input = ""
    if 'selected_json_file' not in st.session_state:
        st.session_state.selected_json_file = None

    # 두 개의 주요 컬럼으로 레이아웃 구성
    left_col, right_col = st.columns([1, 2])

    with left_col:
        lecture_name = st.selectbox(
            "강의 선택",
            st.session_state.lecture_names,
            key="lecture_name",
            index=None,
            placeholder="강의를 선택해주세요",
            disabled=st.session_state.timer_running
        )
        
        if not st.session_state.lecture_names:
            st.info("Settings 탭에서 강의를 추가해주세요.")
        
        # 기존 JSON 파일 선택
        json_files = get_existing_json_files(lecture_name) if lecture_name else []
        json_options = ["새 기록 시작"] + json_files
        selected_json = st.selectbox(
            "기록 선택",
            json_options,
            key="json_file_select",
            on_change=lambda: load_selected_json(lecture_name, json_files, json_options),
            disabled=st.session_state.timer_running
        )

        def load_selected_json(lecture_name, json_files, json_options):
            """선택한 JSON 파일 로드 및 세션 상태 업데이트"""
            selected_index = json_options.index(st.session_state.json_file_select)
            if selected_index == 0:  # 새 기록 시작
                st.session_state.records = []
                st.session_state.slide_number = 1
                st.session_state.last_slide_start_time = None
                st.session_state.elapsed_time = 0
                st.session_state.start_time = None
                st.session_state.start_time_value = "00:00:00.000"
                st.session_state.selected_json_file = None
            else:
                file_name = json_files[selected_index - 1]
                records = load_records(lecture_name, file_name)
                if records:
                    st.session_state.records = records
                    st.session_state.selected_json_file = file_name
                    last_slide = max([int(r["slide_number"]) for r in records], default=0)
                    st.session_state.slide_number = last_slide + 1
                    last_record = records[-1]
                    st.session_state.last_slide_start_time = last_record["end_time"]
                    try:
                        start_time_str = last_record["end_time"]
                        st.session_state.start_time = datetime.strptime(start_time_str, "%H:%M:%S.%f")
                        st.session_state.start_time_value = start_time_str
                        last_end_time = datetime.strptime(last_record["end_time"], "%H:%M:%S.%f")
                        st.session_state.elapsed_time = (last_end_time - st.session_state.start_time).total_seconds() * 1000
                    except ValueError:
                        st.session_state.start_time = None
                        st.session_state.start_time_value = "00:00:00.000"
                        st.session_state.elapsed_time = 0
                else:
                    st.session_state.records = []
                    st.session_state.slide_number = 1
                    st.session_state.last_slide_start_time = None
                    st.session_state.elapsed_time = 0
                    st.session_state.start_time = None
                    st.session_state.start_time_value = "00:00:00.000"

        # Stopwatch 섹션
        st.session_state.slide_number = st.number_input("Slide Number", min_value=1, value=st.session_state.slide_number, step=1, key="slide_input")
        start_time_input = st.text_input(
            "Start Time",
            value=st.session_state.start_time_value,
            key="start_time_input",
            disabled=st.session_state.timer_running
        )
        st.session_state.start_time_value = start_time_input
        elapsed_ms = st.session_state.elapsed_time
        if st.session_state.timer_running and st.session_state.timer_start:
            elapsed_ms += (datetime.now() - st.session_state.timer_start).total_seconds() * 1000
        elapsed_seconds = elapsed_ms / 1000
        if st.session_state.start_time:
            absolute_time = st.session_state.start_time + timedelta(seconds=elapsed_seconds)
            initial_time = absolute_time.strftime("%H:%M:%S.%f")[:-3]
        else:
            hours = int(elapsed_seconds // 3600)
            minutes = int((elapsed_seconds % 3600) // 60)
            seconds = int(elapsed_seconds % 60)
            milliseconds = int(elapsed_ms % 1000)
            initial_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

        start_time_ms = 0
        if st.session_state.start_time:
            start_time_ms = (
                st.session_state.start_time.hour * 3600 +
                st.session_state.start_time.minute * 60 +
                st.session_state.start_time.second +
                st.session_state.start_time.microsecond / 1000000
            ) * 1000
        
        timer_html = f"""
        <div id="timer-display" style="font-size: 18px; font-weight: bold; padding: 10px; border: 1px solid #ddd; border-radius: 5px; text-align: center; background-color: var(--background-color, #ffffff); color: var(--text-color, #000000);">{initial_time}</div>
        <script>
            let timerRunning = {str(st.session_state.timer_running).lower()};
            let startTime = new Date().getTime();
            let elapsedTime = {elapsed_ms};
            let baseTimeMs = {start_time_ms};

            function updateTimer() {{
                if (timerRunning) {{
                    let now = new Date().getTime();
                    let elapsedMs = elapsedTime + (now - startTime);
                    let totalMs = baseTimeMs + elapsedMs;
                    let hours = Math.floor(totalMs / (1000 * 3600));
                    let minutes = Math.floor((totalMs % (1000 * 3600)) / (1000 * 60));
                    let seconds = Math.floor((totalMs % (1000 * 60)) / 1000);
                    let milliseconds = Math.floor(totalMs % 1000);
                    let timeStr = hours.toString().padStart(2, '0') + ':' +
                                minutes.toString().padStart(2, '0') + ':' +
                                seconds.toString().padStart(2, '0') + '.' +
                                milliseconds.toString().padStart(3, '0');
                    let display = document.getElementById('timer-display');
                    if (display) {{
                        display.innerText = timeStr;
                    }}
                }}
            }}

            function updateTheme() {{
                const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
                const timerDisplay = document.getElementById('timer-display');
                if (timerDisplay) {{
                    if (isDarkMode) {{
                        timerDisplay.style.backgroundColor = '#1a1a1a';
                        timerDisplay.style.color = '#ffffff';
                    }} else {{
                        timerDisplay.style.backgroundColor = '#ffffff';
                        timerDisplay.style.color = '#000000';
                    }}
                }}
            }}

            updateTheme();
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateTheme);
            let timerInterval = setInterval(updateTimer, 10);
            window.addEventListener('unload', () => clearInterval(timerInterval));
        </script>
        """
        components.html(timer_html, height=60)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            start_button_label = "Resume" if st.session_state.elapsed_time > 0 and not st.session_state.timer_running else "Start"
            if st.button(start_button_label, disabled=st.session_state.timer_running, use_container_width=True):
                try:
                    start_time_str = start_time_input
                    new_start_time = datetime.strptime(start_time_str, "%H:%M:%S.%f")
                    new_start_time = datetime.combine(datetime.now().date(), new_start_time.time())
                    if new_start_time > datetime.now():
                        new_start_time -= timedelta(days=1)
                    
                    current_start_time_str = st.session_state.start_time.strftime("%H:%M:%S.%f")[:-3] if st.session_state.start_time else "00:00:00.000"
                    if start_time_str != current_start_time_str:
                        st.session_state.elapsed_time = 0
                        st.session_state.last_slide_start_time = new_start_time.strftime("%H:%M:%S.%f")[:-3]
                    
                    st.session_state.start_time = new_start_time
                except ValueError:
                    st.session_state.start_time = datetime.combine(datetime.now().date(), datetime.time(0, 0, 0))
                    st.session_state.elapsed_time = 0
                    st.session_state.last_slide_start_time = st.session_state.start_time.strftime("%H:%M:%S.%f")[:-3]
                
                st.session_state.timer_running = True
                st.session_state.timer_start = datetime.now()
                st.rerun()
        with col2:
            if st.button("Pause", disabled=not st.session_state.timer_running, use_container_width=True):
                st.session_state.timer_running = False
                if st.session_state.timer_start:
                    st.session_state.elapsed_time += (datetime.now() - st.session_state.timer_start).total_seconds() * 1000
                elapsed_seconds = st.session_state.elapsed_time / 1000
                if st.session_state.start_time:
                    absolute_time = st.session_state.start_time + timedelta(seconds=elapsed_seconds)
                    st.session_state.start_time_value = absolute_time.strftime("%H:%M:%S.%f")[:-3]
                else:
                    hours = int(elapsed_seconds // 3600)
                    minutes = int((elapsed_seconds % 3600) // 60)
                    seconds = int(elapsed_seconds % 60)
                    milliseconds = int(st.session_state.elapsed_time % 1000)
                    st.session_state.start_time_value = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
                st.rerun()
        with col3:
            if st.button("Reset", use_container_width=True):
                st.session_state.timer_running = False
                st.session_state.elapsed_time = 0
                st.session_state.start_time = None
                st.session_state.timer_start = None
                st.session_state.last_slide_start_time = None
                st.session_state.records = []
                st.session_state.slide_number = 1
                st.session_state.start_time_value = "00:00:00.000"
                st.session_state.selected_json_file = None
                st.rerun()

        st.text_input("Notes", value="", key="notes")

        if st.button("Record Time", key="record_button", help="Press to record", type='primary', use_container_width=True, disabled=not lecture_name):
            current_elapsed_ms = st.session_state.elapsed_time
            if st.session_state.timer_running and st.session_state.timer_start:
                current_elapsed_ms += (datetime.now() - st.session_state.timer_start).total_seconds() * 1000
            
            if st.session_state.start_time is None:
                st.session_state.start_time = datetime.combine(datetime.now().date(), datetime.time(0, 0, 0))
            
            elapsed_seconds = current_elapsed_ms / 1000
            current_time = st.session_state.start_time + timedelta(seconds=elapsed_seconds)
            current_time_str = current_time.strftime("%H:%M:%S.%f")[:-3]
            
            start_time = st.session_state.last_slide_start_time if st.session_state.last_slide_start_time else st.session_state.start_time.strftime("%H:%M:%S.%f")[:-3]
            
            st.session_state.records.append({
                "slide_number": str(st.session_state.slide_number),
                "start_time": start_time,
                "end_time": current_time_str,
                "notes": st.session_state.notes
            })
            
            st.session_state.last_slide_start_time = current_time_str
            st.session_state.slide_number += 1
            st.session_state.notes_input = ""
            st.session_state["notes_input"] = ""
            st.rerun()

        if st.button("기록 저장", use_container_width=True, disabled=not st.session_state.records):
            file_name = save_records(lecture_name, st.session_state.records)
            if file_name:
                st.session_state.selected_json_file = file_name
                st.success(f"JSON 파일이 브라우저에 저장되었습니다: {file_name}")

    with right_col:
        st.subheader("Records")
        if st.session_state.records:
            df = pd.DataFrame(st.session_state.records)
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "slide_number": st.column_config.TextColumn("Slide Number", help="슬라이드 번호"),
                    "start_time": st.column_config.TextColumn("Start Time", help="시작 시간"),
                    "end_time": st.column_config.TextColumn("End Time", help="종료 시간"),
                    "notes": st.column_config.TextColumn("Notes", help="메모")
                }
            )
            if edited_df is not None:
                st.session_state.records = edited_df.to_dict('records')
        else:
            st.info("표시할 기록이 없습니다.")