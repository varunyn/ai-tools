"""
Enhanced progress display components using Streamlit's latest features.
"""
import streamlit as st
import time
from typing import Optional


class EnhancedProgressMonitor:
    """
    Enhanced progress monitor with status container and progress bar.
    """
    
    def __init__(self, total_chunks: int = 1):
        """
        Initialize progress monitor.
        
        Args:
            total_chunks: Total number of chunks to process
        """
        self.total_chunks = total_chunks
        self.current_chunk = 0
        self.status_container = None
        self.progress_bar = None
        self.start_time = None
        
    def start(self, label: str = "Processing document"):
        """
        Start the progress display.
        
        Args:
            label: Label for the status container
        """
        self.start_time = time.time()
        self.status_container = st.status(label, expanded=True, state="running")
        with self.status_container:
            self.progress_bar = st.progress(0, text="Initializing...")
            st.write("Starting document processing...")
    
    def update_chunk(self, chunk_num: int, total_chunks: int, message: str = ""):
        """
        Update progress for chunk processing.
        
        Args:
            chunk_num: Current chunk number (1-indexed)
            total_chunks: Total number of chunks
            message: Optional message to display
        """
        if self.progress_bar:
            progress = chunk_num / total_chunks
            text = message or f"Processing chunk {chunk_num} of {total_chunks}"
            self.progress_bar.progress(progress, text=text)
        
        if self.status_container:
            with self.status_container:
                if message:
                    st.write(f"📄 {message}")
    
    def update_finalizing(self, message: str = "Finalizing summary..."):
        """
        Update progress for finalization step.
        
        Args:
            message: Message to display
        """
        if self.progress_bar:
            self.progress_bar.progress(0.95, text=message)
        
        if self.status_container:
            with self.status_container:
                st.write(f"✨ {message}")
    
    def complete(self, success: bool = True, message: str = "Processing complete!"):
        """
        Mark progress as complete.
        
        Args:
            success: Whether processing was successful
            message: Completion message
        """
        if self.progress_bar:
            self.progress_bar.progress(1.0, text=message)
        
        if self.status_container:
            elapsed_time = time.time() - self.start_time if self.start_time else 0
            with self.status_container:
                if success:
                    st.success(f"✅ {message}")
                    st.write(f"⏱️ Total time: {elapsed_time:.1f} seconds")
                else:
                    st.error(f"❌ {message}")
            
            # Update status container state
            self.status_container.update(label=message, state="complete" if success else "error")
    
    def close(self):
        """Close the status container."""
        if self.status_container:
            # Status container will remain visible but collapsed
            pass
