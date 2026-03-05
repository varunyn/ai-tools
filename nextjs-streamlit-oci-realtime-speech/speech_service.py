import oci
from config import OCI_CONFIG, API_CONFIG
import numpy as np
import asyncio
import logging
import traceback
import time
import threading
from collections.abc import Mapping, Sequence
from oci_ai_speech_realtime import RealtimeSpeechClient, RealtimeSpeechClientListener
from oci.ai_speech.models import RealtimeParameters

# Set up logging
logger = logging.getLogger(__name__)


def _value(source: object, key: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)

class SpeechListener(RealtimeSpeechClientListener):
    def __init__(self):
        self.final_segments: list[str] = []
        self.partial_segment = ""
        self.transcription = ""
        self.connected = False
        self.session_id = None
        self.last_activity = time.time()
        logger.info("SpeechListener initialized")

    def on_connect(self):
        logger.info("Connected to Oracle service")
        self.connected = True
        self.last_activity = time.time()

    def on_connect_message(self, connectmessage):
        logger.info(f"Received CONNECT event: {connectmessage}")
        try:
            session_id = _value(connectmessage, "sessionId")
            if session_id is None:
                session_id = _value(connectmessage, "session_id")
            if session_id is not None:
                self.session_id = str(session_id)
            logger.info(f"Session ID: {self.session_id}")
        except Exception as e:
            logger.error(f"Error processing connect message: {str(e)}")

    def on_result(self, result):
        self.last_activity = time.time()
        logger.debug(f"Received result from Oracle: {result}")
        try:
            transcriptions = _value(result, "transcriptions")
            if isinstance(transcriptions, Sequence) and not isinstance(transcriptions, (str, bytes)) and transcriptions:
                transcription = transcriptions[0]
                current_value = _value(transcription, "transcription", "")
                is_final_value = _value(transcription, "isFinal", _value(transcription, "is_final", False))
                current = str(current_value).strip()
                is_final = bool(is_final_value)
                if current:
                    logger.info(f"{'Final' if is_final else 'Partial'} transcription: {current}")
                    if is_final:
                        if not self.final_segments or self.final_segments[-1] != current:
                            self.final_segments.append(current)
                        self.partial_segment = ""
                    else:
                        self.partial_segment = current

                    combined_segments = [*self.final_segments]
                    if self.partial_segment:
                        combined_segments.append(self.partial_segment)
                    self.transcription = " ".join(combined_segments)
                    return {"text": current, "is_final": is_final}
        except Exception as e:
            logger.error(f"Error processing result: {str(e)}")
        return None

    def on_error(self, error):
        logger.error(f"Error message: {error}")

    def on_close(self, error_code, error_message):
        logger.info(f"Connection closed: code={error_code}, reason={error_message}")
        self.connected = False
        self.session_id = None

    def on_ack_message(self, ackmessage):
        logger.debug(f"Ack message: {ackmessage}")

    def on_network_event(self, message):
        logger.debug(f"Network event: {message}")

class SpeechService:
    def __init__(self):
        self.config = oci.config.from_file()
        self.client = None
        self.listener = SpeechListener()
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self._connect_task = None
        logger.info("SpeechService initialized")
        
    def _get_realtime_parameters(self):
        params = RealtimeParameters()
        params.language_code = "en-US"
        params.model_domain = params.MODEL_DOMAIN_GENERIC
        params.partial_silence_threshold_in_ms = 0
        params.final_silence_threshold_in_ms = 1000
        params.encoding = "audio/raw;rate=16000"
        params.stabilize_partial_results = "MEDIUM"
        return params

    async def ensure_connection(self):
        """Ensure we have an active connection with retry logic"""
        if not self.is_connected or not self.client:
            while self.reconnect_attempts < self.max_reconnect_attempts:
                logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                success = await self.initialize_websocket()
                if success:
                    self.reconnect_attempts = 0
                    return True
                self.reconnect_attempts += 1
                await asyncio.sleep(1)  # Wait before retry
            logger.error("Max reconnection attempts reached")
            return False
        return True

    async def initialize_websocket(self):
        try:
            # Cancel any existing connection task and reset client
            if self._connect_task and not self._connect_task.done():
                self._connect_task.cancel()
                try:
                    await self._connect_task
                except asyncio.CancelledError:
                    pass
            if self.client:
                self.client.close()
            self.client = None
            self.listener.connected = False
            self.listener.session_id = None

            realtime_speech_url = f"wss://realtime.aiservice.{OCI_CONFIG['region']}.oci.oraclecloud.com"
            logger.info(f"Connecting to Oracle service: {realtime_speech_url}")

            self.client = RealtimeSpeechClient(
                config=self.config,
                realtime_speech_parameters=self._get_realtime_parameters(),
                listener=self.listener,
                service_endpoint=realtime_speech_url,
                compartment_id=OCI_CONFIG["compartment_id"]
            )

            # connect() runs the message loop and never returns until closed,
            # so launch it as a background task and wait for the CONNECT handshake.
            self._connect_task = asyncio.create_task(self.client.connect())

            logger.info("Waiting for CONNECT event...")
            max_wait_time = 10
            start_time = time.time()
            while not self.listener.session_id and (time.time() - start_time < max_wait_time):
                if self._connect_task.done():
                    logger.error("Connection task ended before CONNECT event received")
                    return False
                await asyncio.sleep(0.2)

            if not self.listener.session_id:
                logger.error("Failed to receive session ID within timeout period")
                return False

            logger.info(f"Successfully connected with session ID: {self.listener.session_id}")
            self.is_connected = True
            return True

        except Exception as e:
            logger.error(f"Error initializing WebSocket: {str(e)}\n{traceback.format_exc()}")
            self.is_connected = False
            return False

    async def connect(self) -> bool:
        """Explicitly establish the WebSocket connection. Call once before sending audio."""
        if self.is_connected and self.listener.session_id:
            return True
        return await self.initialize_websocket()

    async def send_audio(self, audio_chunk: bytes) -> bool:
        """Send one audio chunk to Oracle. Results arrive asynchronously via the listener.
        Returns False if the connection is not ready or the send failed."""
        if not audio_chunk:
            return False

        if not self.is_connected or not self.listener.session_id:
            logger.warning("Cannot send audio - not connected")
            return False

        try:
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            if np.all(audio_data == 0):
                return False
            logger.debug(f"Sending audio chunk: {len(audio_data)} samples, session={self.listener.session_id}")
            client = self.client
            if client is None:
                return False
            await client.send_data(audio_chunk)
            return True
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            self.is_connected = False
            return False

    def get_transcription(self) -> str:
        """Return the latest transcription text accumulated by the listener."""
        return self.listener.transcription

    async def close(self):
        """Close the speech service and cleanup"""
        try:
            logger.info("Starting Oracle Speech service connection closure")
            if self.client:
                try:
                    self.client.close()
                    logger.info("Successfully closed Oracle Speech client")
                except Exception as e:
                    logger.error(f"Error during Oracle client close: {str(e)}")
                finally:
                    self.client = None

            if self._connect_task and not self._connect_task.done():
                self._connect_task.cancel()
                try:
                    await self._connect_task
                except asyncio.CancelledError:
                    pass
                self._connect_task = None

            self.is_connected = False
            self.listener.connected = False
            self.listener.session_id = None
            logger.info("Oracle Speech service connection cleanup completed")
        except Exception as e:
            logger.error(f"Error in speech service closure: {str(e)}")

    def save_transcription(self, transcription: str, filename: str) -> bool:
        """Save transcription to a text file"""
        try:
            with open(filename, 'w') as f:
                f.write(transcription)
            logger.info(f"Transcription saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving transcription: {str(e)}")
            return False


class SpeechServiceThread:
    """Thread-safe wrapper that runs SpeechService in a dedicated event loop thread.

    Owns two background threads:
    - _ws_thread: runs the asyncio event loop that owns the WebSocket connection
    - _audio_thread: continuously reads from AudioHandler and sends chunks to Oracle

    This keeps Streamlit completely out of the audio/async loop — the UI only
    needs to call get_transcription() to read the latest result.
    """

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._service = SpeechService()
        self._ws_thread = threading.Thread(
            target=self._run_loop, daemon=True, name="speech-ws-loop"
        )
        self._ws_thread.start()
        self._audio_thread: threading.Thread | None = None
        self._feeding = False

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def connect(self, timeout: float = 10.0) -> bool:
        """Establish the WebSocket connection. Call once before start_audio_feed."""
        future = asyncio.run_coroutine_threadsafe(self._service.connect(), self._loop)
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            logger.error(f"connect() error: {e}")
            return False

    def start_audio_feed(self, audio_handler) -> None:
        """Start a background thread that continuously reads and sends audio chunks."""
        self._feeding = True
        self._audio_thread = threading.Thread(
            target=self._audio_feed_loop,
            args=(audio_handler,),
            daemon=True,
            name="audio-feed",
        )
        self._audio_thread.start()

    def _audio_feed_loop(self, audio_handler) -> None:
        while self._feeding:
            try:
                chunk = audio_handler.get_audio_chunk()
                if chunk:
                    future = asyncio.run_coroutine_threadsafe(
                        self._service.send_audio(chunk), self._loop
                    )
                    future.result(timeout=1.0)
            except Exception as e:
                logger.error(f"Audio feed error: {e}")
            time.sleep(0.02)

    def stop_audio_feed(self) -> None:
        self._feeding = False
        if self._audio_thread:
            self._audio_thread.join(timeout=2.0)
            self._audio_thread = None

    def get_transcription(self) -> str:
        """Return the latest transcription from the listener (thread-safe read)."""
        return self._service.get_transcription()

    def stop(self, timeout: float = 3.0) -> None:
        """Stop audio feed, close the WebSocket, and shut down the event loop."""
        self.stop_audio_feed()
        future = asyncio.run_coroutine_threadsafe(self._service.close(), self._loop)
        try:
            future.result(timeout=timeout)
        except Exception as e:
            logger.error(f"Error during speech service stop: {e}")
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._ws_thread.join(timeout=timeout)
