import streamlit as st
from config.constants import DEFAULT_PROMPT, MAX_SAVED_PROMPTS
from utils.prompts import save_prompts_to_file


def update_prompt_from_selection() -> None:
    """Update current prompt when user selects a different prompt from dropdown."""
    selected = st.session_state.prompt_selector
    st.session_state.selected_prompt_name = selected
    
    # Update current prompt based on selection
    if selected == "Default Prompt":
        st.session_state.current_prompt = DEFAULT_PROMPT
        st.session_state.editing_prompt_name = ""
    else:
        st.session_state.current_prompt = st.session_state.saved_prompts[selected]
        st.session_state.editing_prompt_name = selected
    
    # Also update the editor text
    st.session_state.prompt_editor = st.session_state.current_prompt
    
    # Set the prompt name for editing
    st.session_state.new_prompt_name = st.session_state.editing_prompt_name


def update_current_prompt_from_editor() -> None:
    """Update current prompt when user edits the prompt template."""
    if 'prompt_editor' in st.session_state:
        st.session_state.current_prompt = st.session_state.prompt_editor


def save_prompt() -> None:
    """Save or update a prompt template."""
    prompt_name = st.session_state.new_prompt_name
    
    # Check if we're editing an existing prompt
    is_editing_existing = (
        st.session_state.editing_prompt_name != "" and 
        st.session_state.editing_prompt_name == prompt_name
    )
    
    # Check prompt limit only for new prompts
    if (not is_editing_existing and
        len(st.session_state.saved_prompts) >= MAX_SAVED_PROMPTS and 
        prompt_name not in st.session_state.saved_prompts):
        st.session_state.save_error = (
            f"Maximum of {MAX_SAVED_PROMPTS} saved prompts reached. "
            "Delete one to save a new prompt."
        )
        return
    
    if not prompt_name:
        st.session_state.save_error = "Please enter a name for the prompt"
        return
    
    # Save the prompt
    st.session_state.saved_prompts[prompt_name] = st.session_state.current_prompt
    save_prompts_to_file(st.session_state.saved_prompts)
    
    # If we're updating an existing prompt but with a new name, delete the old one
    if (st.session_state.editing_prompt_name != "" and 
        st.session_state.editing_prompt_name != prompt_name):
        del st.session_state.saved_prompts[st.session_state.editing_prompt_name]
        save_prompts_to_file(st.session_state.saved_prompts)
        st.toast(f"Prompt renamed to '{prompt_name}' and updated!", icon="✅")
    elif is_editing_existing:
        st.toast(f"Prompt '{prompt_name}' updated!", icon="✅")
    else:
        st.toast(f"Prompt '{prompt_name}' saved!", icon="✅")
    
    st.session_state.selected_prompt_name = prompt_name
    st.session_state.editing_prompt_name = prompt_name


def delete_prompt() -> None:
    """Delete a saved prompt."""
    prompt_name = st.session_state.selected_prompt_name
    if prompt_name != "Default Prompt":
        del st.session_state.saved_prompts[prompt_name]
        save_prompts_to_file(st.session_state.saved_prompts)
        st.session_state.selected_prompt_name = "Default Prompt"
        st.session_state.current_prompt = DEFAULT_PROMPT
        st.session_state.prompt_editor = DEFAULT_PROMPT
        st.session_state.editing_prompt_name = ""
        st.session_state.new_prompt_name = ""
        st.toast(f"Prompt '{prompt_name}' deleted!", icon="🗑️")


def toggle_copy_view() -> None:
    """Toggle between formatted and copyable view of summary."""
    st.session_state.show_copy_view = not st.session_state.show_copy_view


def update_selected_model() -> None:
    """Reset processed file and summary when model changes."""
    if 'processed_file' in st.session_state:
        del st.session_state.processed_file
    if 'generated_summary' in st.session_state:
        st.session_state.generated_summary = ""
