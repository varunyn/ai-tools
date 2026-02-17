"""
Main content area UI components.

The main panel shows summary and stats when a document is uploaded (from the sidebar);
otherwise it shows an empty state with instructions.
"""
import streamlit as st
from components.file_stats import display_file_stats
from components.summary_stats import display_summary_stats


def render_main_panel(
    uploaded_file,
    file_content: str | None = None,
    file_size: int | None = None,
) -> None:
    """
    Render the main panel: empty state or summary + stats.

    Args:
        uploaded_file: The uploaded file from sidebar, or None.
        file_content: Decoded file content (required when uploaded_file is set).
        file_size: File size in bytes (optional, derived from uploaded_file if not set).
    """
    if uploaded_file is None:
        _render_empty_state()
        return

    if file_content is None:
        st.error("Could not read the uploaded file. Please try another file.")
        return

    if file_size is None:
        file_size = len(uploaded_file.getvalue())

    render_file_info(uploaded_file, file_content, file_size)
    render_summary_section(uploaded_file)


def _render_empty_state() -> None:
    """Render the main panel when no file has been uploaded."""
    st.markdown("## Summary & statistics")
    st.markdown(
        "Upload a document from the **sidebar** (Prompt Management, Model Settings, "
        "and Upload Document) to generate an AI-powered summary. Your summary and "
        "statistics will appear here."
    )
    st.divider()
    st.info("👈 Open the sidebar and use **Upload Document** to get started.")


def render_file_info(uploaded_file, file_content: str, file_size: int) -> None:
    """
    Render file information and statistics.
    
    Args:
        uploaded_file: The uploaded file object
        file_content: Content of the file as string
        file_size: Size of the file in bytes
    """
    st.success(f"✅ File uploaded: **{uploaded_file.name}**")
    display_file_stats(uploaded_file.name, file_size, file_content)
    st.divider()


def render_summary_section(uploaded_file) -> None:
    """
    Render the generated summary with statistics and actions.
    
    Args:
        uploaded_file: The uploaded file object (for download filename)
    """
    if not st.session_state.generated_summary:
        return
    
    st.divider()
    st.subheader("📄 Generated Summary")
    
    # Display summary statistics
    summary_length = len(st.session_state.generated_summary)
    original_length = st.session_state.get('original_length', summary_length)
    processing_time = st.session_state.get('processing_time', None)
    
    display_summary_stats(
        original_length=original_length,
        summary_length=summary_length,
        model_name=st.session_state.selected_model,
        processing_time=processing_time
    )
    
    st.divider()
    
    # Action buttons
    _render_summary_actions(uploaded_file)
    
    # Summary content
    _render_summary_content()
    
    # Feedback widget
    _render_feedback_section()


def _render_summary_actions(uploaded_file) -> None:
    """Render action buttons for summary (copy, download)."""
    col_copy, col_view = st.columns(2)
    with col_copy:
        button_text = (
            "📋 Copy to Clipboard" 
            if not st.session_state.show_copy_view 
            else "🔙 Back to Formatted View"
        )
        from utils.callbacks import toggle_copy_view
        st.button(
            button_text,
            on_click=toggle_copy_view,
            use_container_width=True
        )
    
    with col_view:
        # Export functionality
        summary_text = st.session_state.generated_summary
        st.download_button(
            label="💾 Download as TXT",
            data=summary_text,
            file_name=f"summary_{uploaded_file.name if uploaded_file else 'summary'}.txt",
            mime="text/plain",
            use_container_width=True
        )


def _render_summary_content() -> None:
    """Render the summary content in formatted or copyable view."""
    if st.session_state.show_copy_view:
        # Show the plain text version for easy copying
        st.code(st.session_state.generated_summary, language="markdown")
        st.info(
            "👆 The summary is displayed above in a copyable format. "
            "Select all the text (Ctrl+A or Cmd+A) and copy (Ctrl+C or Cmd+C)."
        )
    else:
        # Display the summary in a styled box
        st.markdown(f"""
        <div class="summary-box">
            {st.session_state.generated_summary}
        </div>
        """, unsafe_allow_html=True)


def _render_feedback_section() -> None:
    """Render the feedback widget section."""
    st.divider()
    st.caption("How would you rate this summary?")
    feedback = st.feedback("thumbs", key="summary_feedback")
    if feedback is not None:
        st.toast("Thank you for your feedback!", icon="👍")
