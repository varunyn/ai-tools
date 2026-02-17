"""
File processing and summary generation utilities.

Uses unified OCI Gen AI inference (GenericChatRequest + model_id) for all models.
"""
import os
import time
import threading
from typing import Optional, Tuple

import streamlit as st

from config.constants import (
    GENAI_MODELS,
    TEMP_DATA_FILE,
    PROGRESS_FILE,
    CHUNK_SIZE_CHARS,
    LARGE_DOCUMENT_THRESHOLD,
    PROGRESS_UPDATE_INTERVAL,
    MONITOR_THREAD_TIMEOUT,
)
from components.progress_display import EnhancedProgressMonitor
from components.error_display import display_user_friendly_error
from utils.genai_inference import summarize_with_model
from utils.logger import get_logger

logger = get_logger(__name__)


def process_file_with_model(
    uploaded_file,
    file_content: str,
    model_name: str,
    debug_mode: bool = False,
) -> Tuple[Optional[str], Optional[float]]:
    """
    Process uploaded file and generate summary using the selected model.

    Args:
        uploaded_file: The uploaded file object
        file_content: Content of the file as string
        model_name: Display name of the model (key in GENAI_MODELS)
        debug_mode: Whether to enable debug mode (unused; kept for API compatibility)

    Returns:
        Tuple of (summary text, processing time in seconds) or (None, None) on error
    """
    processing_start_time = time.time()
    model_id = GENAI_MODELS.get(model_name)
    if not model_id:
        logger.warning(f"Unknown model {model_name}, using first available")
        model_id = next(iter(GENAI_MODELS.values()))

    prompt_template = st.session_state.current_prompt
    is_long = len(file_content) > LARGE_DOCUMENT_THRESHOLD

    try:
        if is_long:
            summary = _process_long_document(
                model_id=model_id,
                file_content=file_content,
                prompt_template=prompt_template,
            )
        else:
            with st.spinner("Generating summary..."):
                summary = summarize_with_model(
                    model_id=model_id,
                    text=file_content,
                    prompt_template=prompt_template,
                )
            st.toast("Summary generated successfully!", icon="✅")

        processing_time = time.time() - processing_start_time
        logger.info(f"Summary generated in {processing_time:.2f}s with {model_id}")
        return summary, processing_time

    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        display_user_friendly_error(
            e, context="Summary generation", show_details=debug_mode
        )
        return None, None
    finally:
        _cleanup_temp_files()


def _process_long_document(
    model_id: str,
    file_content: str,
    prompt_template: str,
) -> str:
    """Run chunked summarization with progress UI."""
    estimated_chunks = max(1, len(file_content) // CHUNK_SIZE_CHARS)
    progress_monitor = EnhancedProgressMonitor(total_chunks=estimated_chunks)
    progress_monitor.start("Processing document in chunks")

    stop_flag = [False]

    def monitor_progress() -> None:
        last_progress = ""
        while not stop_flag[0] and os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r") as f:
                    progress_text = f.read().strip()
                if progress_text != last_progress:
                    last_progress = progress_text
                    if "/" in progress_text and "Finalizing" not in progress_text:
                        try:
                            current, total = progress_text.split("/")
                            progress_monitor.update_chunk(
                                int(current),
                                int(total),
                                f"Processing chunk {current} of {total}",
                            )
                        except (ValueError, TypeError):
                            if progress_monitor.status_container:
                                with progress_monitor.status_container:
                                    st.write(f"🔄 {progress_text}")
                    elif "Finalizing" in progress_text:
                        progress_monitor.update_finalizing(progress_text)
            except (FileNotFoundError, OSError):
                pass
            except Exception as e:
                logger.warning(f"Progress monitor: {e}")
            time.sleep(PROGRESS_UPDATE_INTERVAL)

    monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
    monitor_thread.start()

    try:
        summary = summarize_with_model(
            model_id=model_id,
            text=file_content,
            prompt_template=prompt_template,
            progress_file=PROGRESS_FILE,
        )
        stop_flag[0] = True
        progress_monitor.complete(True, "Summary generated successfully!")
        return summary
    except Exception:
        stop_flag[0] = True
        if progress_monitor.status_container:
            progress_monitor.complete(False, "Error generating summary")
        raise
    finally:
        monitor_thread.join(timeout=MONITOR_THREAD_TIMEOUT)
        progress_monitor.close()


def _cleanup_temp_files() -> None:
    """Clean up temporary files created during processing."""
    for file_path in [TEMP_DATA_FILE, "prompt.txt", PROGRESS_FILE]:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except (FileNotFoundError, OSError, PermissionError) as e:
            logger.warning(f"Cleanup {file_path}: {e}")
        except Exception as e:
            logger.error(f"Cleanup {file_path}: {e}", exc_info=True)
