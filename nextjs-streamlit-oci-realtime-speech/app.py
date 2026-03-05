import json
import logging

import streamlit as st
import streamlit.components.v1 as components

from audio_handler import AudioHandler
from config import OCI_CONFIG
from speech_service import SpeechServiceThread

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Real-time Speech Transcription", page_icon="🎤", layout="centered")

STATE_DEFAULTS: dict[str, object] = {
    "transcription": "",
    "is_recording": False,
    "audio_handler": None,
    "speech_service": None,
    "connection_error": False,
    "last_error": None,
}


def init_state() -> None:
    for key, default in STATE_DEFAULTS.items():
        st.session_state.setdefault(key, default)


def reset_error_state() -> None:
    st.session_state.connection_error = False
    st.session_state.last_error = None


def cleanup_resources() -> None:
    service = st.session_state.speech_service
    audio_handler = st.session_state.audio_handler

    if service:
        try:
            service.stop()
        except Exception:
            logger.exception("Error stopping speech service")

    if audio_handler:
        try:
            audio_handler.stop_recording()
        except Exception:
            logger.exception("Error stopping audio handler")

    st.session_state.speech_service = None
    st.session_state.audio_handler = None
    st.session_state.is_recording = False


def start_recording() -> None:
    if st.session_state.is_recording:
        return

    reset_error_state()
    st.session_state.transcription = ""
    service = None
    audio_handler = None

    try:
        service = SpeechServiceThread()
        if not service.connect(timeout=10.0):
            st.session_state.connection_error = True
            st.session_state.last_error = "Could not connect to Oracle Speech service."
            logger.error("Failed to connect to Oracle Speech service")
            return

        audio_handler = AudioHandler()
        audio_handler.start_recording()
        service.start_audio_feed(audio_handler)

        st.session_state.speech_service = service
        st.session_state.audio_handler = audio_handler
        st.session_state.is_recording = True
        logger.info("Recording session started")
    except Exception:
        logger.exception("Error starting recording")
        st.session_state.connection_error = True
        st.session_state.last_error = "Failed to start recording. Check your audio device and OCI settings."

        if audio_handler:
            try:
                audio_handler.stop_recording()
            except Exception:
                logger.exception("Failed to stop audio handler after start failure")

        if service:
            try:
                service.stop()
            except Exception:
                logger.exception("Failed to stop speech service after start failure")
    finally:
        if not st.session_state.is_recording:
            st.session_state.speech_service = None
            st.session_state.audio_handler = None


def stop_recording() -> None:
    cleanup_resources()
    logger.info("Recording stopped")


def clear_transcription() -> None:
    st.session_state.transcription = ""
    reset_error_state()


def show_config_validation() -> None:
    missing_keys = [key for key, value in OCI_CONFIG.items() if not value]
    if missing_keys:
        st.warning(
            "Missing OCI configuration values: " + ", ".join(missing_keys),
            icon="⚠️",
        )


def render_copy_button(text: str) -> None:
    payload = json.dumps(text)
    components.html(
        f"""
        <button id=\"copy-transcript\" style=\"width:100%;padding:0.45rem 0.7rem;border:1px solid #d1d5db;border-radius:0.5rem;background:#ffffff;cursor:pointer;\">📋 Copy transcript</button>
        <script>
        const btn = document.getElementById('copy-transcript');
        btn.addEventListener('click', async () => {{
            try {{
                await navigator.clipboard.writeText({payload});
                btn.textContent = '✅ Copied';
                setTimeout(() => {{ btn.textContent = '📋 Copy transcript'; }}, 1400);
            }} catch (e) {{
                btn.textContent = '❌ Copy failed';
                setTimeout(() => {{ btn.textContent = '📋 Copy transcript'; }}, 1400);
            }}
        }});
        </script>
        """,
        height=44,
    )


@st.fragment(run_every=1)
def transcription_display() -> None:
    if st.session_state.is_recording and st.session_state.speech_service:
        latest = st.session_state.speech_service.get_transcription()
        if latest:
            st.session_state.transcription = latest

    text = st.session_state.transcription
    if text:
        st.text_area("Transcript", value=text, height=220, disabled=True)
        words = len(text.split())
        chars = len(text)
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Words", words)
        with metric_col2:
            st.metric("Characters", chars)

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            render_copy_button(text)
        with action_col2:
            st.download_button(
                label="⬇️ Download transcript",
                data=text,
                file_name="transcription.txt",
                mime="text/plain",
                use_container_width=True,
            )
    else:
        st.info("No transcription yet — start recording and speak.")


init_state()

st.title("🎤 Real-time Speech Transcription")
st.caption("Start recording to stream your microphone to Oracle Speech and view live transcript updates.")
show_config_validation()

action_col, clear_col, status_col = st.columns([1, 1, 2])

with action_col:
    if st.session_state.is_recording:
        st.button("⏹️ Stop", use_container_width=True, on_click=stop_recording)
    else:
        st.button("🎤 Record", use_container_width=True, on_click=start_recording)

with clear_col:
    st.button(
        "🧹 Clear",
        use_container_width=True,
        on_click=clear_transcription,
        disabled=st.session_state.is_recording,
    )

with status_col:
    if st.session_state.is_recording:
        st.success("Recording in progress...")
    elif st.session_state.connection_error:
        st.error(st.session_state.last_error or "Could not connect to Oracle Speech service.")
    else:
        st.write("Ready")

transcription_display()
