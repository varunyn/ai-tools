import streamlit as st
from config.constants import GENAI_MODELS, MODEL_DESCRIPTIONS, MAX_FILE_SIZE_MB
from utils.callbacks import (
    update_prompt_from_selection,
    save_prompt,
    delete_prompt,
    update_selected_model,
    update_current_prompt_from_editor
)


def render_sidebar() -> None:
    with st.sidebar:
        st.title("📝 Text Summarizer")
        st.caption("OCI Generative AI")
        st.divider()

        # Prompt Management Section
        _render_prompt_management()

        st.divider()

        # Model Selection Section
        _render_model_settings()

        st.divider()

        # Upload Document Section
        _render_file_upload()

        st.divider()

        # App Info
        _render_app_info()


def _render_prompt_management() -> None:
    st.subheader("Prompt Management")
    
    prompt_names = ["Default Prompt"] + list(st.session_state.saved_prompts.keys())
    selected_index = (
        prompt_names.index(st.session_state.selected_prompt_name) 
        if st.session_state.selected_prompt_name in prompt_names 
        else 0
    )
    
    st.selectbox(
        "Select a Prompt",
        prompt_names,
        key="prompt_selector",
        on_change=update_prompt_from_selection,
        index=selected_index,
        help="Choose a saved prompt or use the default"
    )
    
    with st.expander("✏️ Edit Prompt", expanded=False):
        if 'prompt_editor' not in st.session_state:
            st.session_state.prompt_editor = st.session_state.current_prompt
            
        st.text_area(
            "Prompt Template",
            key="prompt_editor",
            value=st.session_state.current_prompt,
            height=200,
            help="Use {} as a placeholder for the text content",
            on_change=update_current_prompt_from_editor,
            label_visibility="visible"
        )
    
    st.divider()
    st.subheader("Save Prompt")
    
    name_value = st.session_state.editing_prompt_name
    st.text_input(
        "Prompt Name", 
        key="new_prompt_name", 
        value=name_value, 
        help="Enter a name for your custom prompt"
    )
    
    save_text = "💾 Update Prompt" if name_value and name_value != "Default Prompt" else "💾 Save Prompt"
    
    col_save, col_delete = st.columns(2)
    with col_save:
        st.button(save_text, on_click=save_prompt, use_container_width=True)
    with col_delete:
        if st.session_state.selected_prompt_name != "Default Prompt":
            st.button("🗑️", on_click=delete_prompt, use_container_width=True, help="Delete prompt")
    
    if hasattr(st.session_state, 'save_error'):
        st.error(st.session_state.save_error)
        delattr(st.session_state, 'save_error')


def _render_model_settings() -> None:
    st.subheader("Model Settings")
    
    model_names = list(GENAI_MODELS.keys())
    st.selectbox(
        "AI Model",
        options=model_names,
        key="selected_model",
        on_change=update_selected_model,
        index=model_names.index(st.session_state.selected_model)
        if st.session_state.selected_model in model_names
        else 0,
        help="Select the AI model for summarization",
    )

    with st.expander("⚙️ Advanced Options", expanded=False):
        model_id = GENAI_MODELS.get(st.session_state.selected_model, "")
        if model_id.startswith("meta."):
            debug_enabled = st.checkbox(
                "Debug Mode",
                value=st.session_state.get("debug_mode", False),
                help="Show detailed API responses",
                key="debug_checkbox",
            )
            st.session_state.debug_mode = debug_enabled

    desc = MODEL_DESCRIPTIONS.get(
        st.session_state.selected_model, "OCI Generative AI model."
    )
    st.info(f"**{st.session_state.selected_model}**: {desc}")


def _render_file_upload() -> None:
    st.subheader("📤 Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a text file",
        type=["txt"],
        help=f"Upload a text file (TXT format, max {MAX_FILE_SIZE_MB}MB)",
        key="sidebar_file_uploader",
    )

    if uploaded_file is not None:
        size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            st.error(
                f"File is too large ({size_mb:.1f}MB). Max allowed is {MAX_FILE_SIZE_MB}MB."
            )
            st.session_state.sidebar_file_uploader = None
            uploaded_file = None

    st.session_state.uploaded_file = uploaded_file


def _render_app_info() -> None:
    with st.expander("ℹ️ About", expanded=False):
        st.caption("Text Summarizer v1.0")
        st.caption("Powered by OCI Generative AI")
        st.caption(f"Upload text files up to {MAX_FILE_SIZE_MB}MB")
