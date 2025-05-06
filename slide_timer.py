import streamlit as st
import json
from s3_utils import save_json_to_s3, load_json_from_s3

def lecture_timer_tab():
    """Render the Slide Timer tab with JSON data handling."""
    # Initialize session state for timer data if not present
    if 'timer_data' not in st.session_state:
        st.session_state.timer_data = {
            'slides': [],
            'current_slide': 0,
            'total_time': 0
        }

    # Load existing JSON data based on authentication
    if st.session_state.get('is_authenticated', False) and st.session_state.get('user_id'):
        try:
            # Load from S3 for authenticated users
            json_data = load_json_from_s3(st.session_state.user_id, 'timer_data.json')
            if json_data:
                st.session_state.timer_data = json_data.get('timer_data', st.session_state.timer_data)
        except Exception as e:
            st.warning(f"Failed to load timer data from S3: {e}")
    else:
        # Use session state for guest users
        pass  # Data already in st.session_state.timer_data

    st.header("Slide Timer")
    
    # Slide management interface
    with st.form(key='slide_form'):
        slide_count = st.number_input("Number of slides", min_value=1, max_value=100, value=len(st.session_state.timer_data['slides']) or 1)
        submit = st.form_submit_button("Update Slides")
        
        if submit:
            # Adjust slide list
            current_slides = st.session_state.timer_data['slides']
            new_slides = [{'number': i+1, 'time': current_slides[i]['time'] if i < len(current_slides) else 0} for i in range(slide_count)]
            st.session_state.timer_data['slides'] = new_slides
            
            # Save data based on authentication
            if st.session_state.get('is_authenticated', False) and st.session_state.get('user_id'):
                try:
                    save_json_to_s3(st.session_state.user_id, st.session_state.timer_data, 'timer_data.json')
                except Exception as e:
                    st.error(f"Failed to save timer data to S3: {e}")
            else:
                # For guests, data is already in session state
                pass

    # Display slides and timers
    for slide in st.session_state.timer_data['slides']:
        st.markdown(f"<div class='slide-number'>Slide {slide['number']}</div>", unsafe_allow_html=True)
        slide['time'] = st.number_input(f"Time (seconds) for Slide {slide['number']}", min_value=0, value=slide['time'], key=f"time_{slide['number']}")
        
        # Update total time
        st.session_state.timer_data['total_time'] = sum(slide['time'] for slide in st.session_state.timer_data['slides'])
        
        # Save on change
        if st.session_state.get('is_authenticated', False) and st.session_state.get('user_id'):
            try:
                save_json_to_s3(st.session_state.user_id, st.session_state.timer_data, 'timer_data.json')
            except Exception as e:
                st.error(f"Failed to save timer data to S3: {e}")

    # Display total time
    st.write(f"Total Presentation Time: {st.session_state.timer_data['total_time']} seconds")