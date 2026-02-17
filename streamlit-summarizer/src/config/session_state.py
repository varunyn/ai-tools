import streamlit as st
from config.constants import DEFAULT_PROMPT, GENAI_MODELS
from utils.prompts import load_saved_prompts


def initialize_session_state() -> None:
    if 'saved_prompts' not in st.session_state:
        st.session_state.saved_prompts = load_saved_prompts()
    
    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = DEFAULT_PROMPT
    
    if 'selected_prompt_name' not in st.session_state:
        st.session_state.selected_prompt_name = "Default Prompt"
    
    if 'editing_prompt_name' not in st.session_state:
        st.session_state.editing_prompt_name = ""
    
    if 'generated_summary' not in st.session_state:
        st.session_state.generated_summary = ""
    
    if 'processed_file' not in st.session_state:
        st.session_state.processed_file = None
    
    if 'processing_time' not in st.session_state:
        st.session_state.processing_time = None
    
    if 'original_length' not in st.session_state:
        st.session_state.original_length = 0
    
    if 'show_copy_view' not in st.session_state:
        st.session_state.show_copy_view = False
    
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = list(GENAI_MODELS.keys())[0]
    
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
