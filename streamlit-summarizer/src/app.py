import streamlit as st
import logging

from utils.logger import setup_logging
from config.constants import APP_NAME, APP_ICON
from config.session_state import initialize_session_state
from utils.styles import CUSTOM_CSS
from ui.sidebar import render_sidebar
from ui.main_content import render_main_panel
from utils.processing import process_file_with_model

setup_logging(log_dir="logs", log_level=logging.INFO)

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide"
)

st.html(CUSTOM_CSS)

initialize_session_state()

render_sidebar()

uploaded_file = st.session_state.get("uploaded_file")

if uploaded_file is None:
    for key in ("generated_summary", "processed_file", "processing_time", "original_length"):
        if key in st.session_state:
            del st.session_state[key]
    render_main_panel(None)
else:
    try:
        file_content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        file_content = uploaded_file.read().decode("utf-8", errors="replace")
    uploaded_file.seek(0)
    file_size = len(uploaded_file.getvalue())

    if (
        "processed_file" not in st.session_state
        or st.session_state.processed_file != uploaded_file.name
    ):
        summary, processing_time = process_file_with_model(
            uploaded_file=uploaded_file,
            file_content=file_content,
            model_name=st.session_state.selected_model,
            debug_mode=st.session_state.get("debug_mode", False),
        )
        if summary:
            st.session_state.generated_summary = summary
            st.session_state.processed_file = uploaded_file.name
            st.session_state.processing_time = processing_time
            st.session_state.original_length = len(file_content)
        else:
            st.session_state.generated_summary = ""

    render_main_panel(uploaded_file, file_content=file_content, file_size=file_size)
