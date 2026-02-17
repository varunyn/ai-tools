"""
Summary statistics component for displaying summary metadata and metrics.
"""
import streamlit as st
from typing import Optional


def display_summary_stats(
    original_length: int,
    summary_length: int,
    model_name: str,
    processing_time: Optional[float] = None,
    compact: bool = True,
) -> None:
    """
    Display summary statistics in a formatted card.

    Args:
        original_length: Character count of original text
        summary_length: Character count of summary
        model_name: Name of the model used
        processing_time: Optional processing time in seconds
        compact: If True, show a single-line compact bar; else use st.metric columns.
    """
    compression_ratio = (
        (1 - summary_length / original_length) * 100 if original_length > 0 else 0
    )

    if compact:
        parts = [
            f"{original_length:,} → {summary_length:,} chars",
            f"{compression_ratio:.1f}% compression",
            model_name,
        ]
        if processing_time is not None:
            parts.append(f"{processing_time:.1f}s")
        st.caption(" · ".join(parts))
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Original Length", f"{original_length:,} chars")
        with col2:
            st.metric("Summary Length", f"{summary_length:,} chars")
        with col3:
            st.metric("Compression", f"{compression_ratio:.1f}%")
        with col4:
            if processing_time is not None:
                st.metric("Processing Time", f"{processing_time:.1f}s")
            else:
                st.metric("Model", model_name)
        if processing_time is not None:
            st.caption(
                f"🤖 Model: {model_name} | ⏱️ Processed in {processing_time:.1f} seconds"
            )
