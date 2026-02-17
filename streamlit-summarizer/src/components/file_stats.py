"""
File statistics component for displaying file metadata.
"""
import streamlit as st
from typing import Optional


def display_file_stats(
    file_name: str,
    file_size: int,
    content: Optional[str] = None,
    compact: bool = True,
) -> None:
    """
    Display file statistics in a formatted card.

    Args:
        file_name: Name of the uploaded file
        file_size: Size of the file in bytes
        content: Optional file content to calculate additional stats
        compact: If True, show a single-line compact bar; else use st.metric columns.
    """
    if file_size < 1024:
        size_str = f"{file_size} B"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"

    char_count = len(content) if content else None
    word_count = len(content.split()) if content else None
    estimated_reading_time = None
    if word_count:
        estimated_reading_time = max(1, round(word_count / 200))

    if compact:
        name_short = (file_name[:28] + "…") if len(file_name) > 30 else file_name
        parts = [
            f"**{name_short}**",
            size_str,
            f"{char_count:,} chars" if char_count is not None else "—",
            f"{word_count:,} words" if word_count is not None else "—",
        ]
        if estimated_reading_time:
            parts.append(f"~{estimated_reading_time} min read")
        st.caption(" · ".join(parts))
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("File Name", (file_name[:30] + "...") if len(file_name) > 30 else file_name)
        with col2:
            st.metric("File Size", size_str)
        with col3:
            st.metric("Characters", f"{char_count:,}" if char_count is not None else "N/A")
        with col4:
            st.metric("Words", f"{word_count:,}" if word_count is not None else "N/A")
        if estimated_reading_time:
            st.caption(
                f"📖 Estimated reading time: {estimated_reading_time} minute{'s' if estimated_reading_time > 1 else ''}"
            )
