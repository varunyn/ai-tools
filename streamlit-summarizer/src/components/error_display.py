"""
User-friendly error display components.
"""
import streamlit as st
from typing import Optional


def display_user_friendly_error(
    error: Exception,
    context: Optional[str] = None,
    show_details: bool = False
) -> None:
    """
    Display a user-friendly error message with recovery suggestions.
    
    Args:
        error: The exception that occurred
        context: Optional context about where the error occurred
        show_details: Whether to show technical details (for debug mode)
    """
    error_type = type(error).__name__
    
    # User-friendly error messages based on error type
    error_messages = {
        "FileNotFoundError": {
            "title": "File Not Found",
            "message": "The requested file could not be found.",
            "suggestions": [
                "Check that the file path is correct",
                "Ensure the file exists in the expected location",
                "Verify file permissions"
            ]
        },
        "PermissionError": {
            "title": "Permission Denied",
            "message": "You don't have permission to access this file.",
            "suggestions": [
                "Check file permissions",
                "Ensure you have read/write access",
                "Try running with appropriate permissions"
            ]
        },
        "OSError": {
            "title": "File System Error",
            "message": "An error occurred while accessing the file system.",
            "suggestions": [
                "Check available disk space",
                "Verify file system permissions",
                "Ensure the file is not locked by another process"
            ]
        },
        "json.JSONDecodeError": {
            "title": "Invalid File Format",
            "message": "The file could not be parsed. It may be corrupted or in an unsupported format.",
            "suggestions": [
                "Verify the file is a valid text file",
                "Check for encoding issues",
                "Try re-saving the file"
            ]
        },
        "ValueError": {
            "title": "Invalid Input",
            "message": "The provided input is not valid.",
            "suggestions": [
                "Check your input format",
                "Verify all required fields are filled",
                "Review the input requirements"
            ]
        }
    }
    
    # Get error info
    error_info = error_messages.get(error_type, {
        "title": "An Error Occurred",
        "message": str(error),
        "suggestions": [
            "Please try again",
            "Check your input and try again",
            "Contact support if the problem persists"
        ]
    })
    
    # Display error
    with st.container():
        st.error(f"**{error_info['title']}**")
        st.write(error_info['message'])
        
        if context:
            st.caption(f"Context: {context}")
        
        # Show suggestions
        with st.expander("💡 What can I do?", expanded=True):
            for suggestion in error_info['suggestions']:
                st.write(f"• {suggestion}")
        
        # Show technical details if requested
        if show_details:
            with st.expander("🔧 Technical Details", expanded=False):
                st.exception(error)
        
        # Add retry button for certain errors
        if error_type in ["FileNotFoundError", "PermissionError", "OSError"]:
            st.button("🔄 Try Again", key="error_retry_button")
