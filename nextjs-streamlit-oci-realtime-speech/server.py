import asyncio
import websockets
import json
import logging
from speech_service import SpeechService
import os
from typing import cast
from websockets.exceptions import ConnectionClosed
from websockets.asyncio.server import ServerConnection
from websockets.http11 import Request, Response
from websockets.datastructures import Headers

from config import OCI_CONFIG
from message_schema import (
    health_payload,
    readiness_payload,
    ws_connection_closed,
    ws_error,
    ws_session_started,
    ws_session_stopped,
    ws_transcription,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Starting websocket transcription server")

# Global instances
speech_services: dict[str, SpeechService] = {}


def _json_response(status_code: int, payload: dict[str, object]) -> Response:
    body = json.dumps(payload).encode("utf-8")
    headers = Headers(
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ]
    )
    reason = "OK" if status_code == 200 else "Service Unavailable"
    return Response(status_code=status_code, reason_phrase=reason, headers=headers, body=body)


def _readiness_state() -> tuple[bool, str | None]:
    required_keys = ["user", "key_file", "fingerprint", "tenancy", "region", "compartment_id"]
    missing = [key for key in required_keys if not OCI_CONFIG.get(key)]
    if missing:
        return False, f"Missing OCI config values: {', '.join(missing)}"

    key_file = OCI_CONFIG.get("key_file")
    if not isinstance(key_file, str) or not os.path.exists(key_file):
        return False, "OCI key file is not present"

    return True, None


def _http_health(request: Request) -> Response | None:
    if request.path == "/health":
        return _json_response(200, health_payload())

    if request.path == "/ready":
        ready, reason = _readiness_state()
        return _json_response(200 if ready else 503, readiness_payload(ready, reason))

    return None


async def process_request(_connection: ServerConnection, request: Request) -> Response | None:
    return _http_health(request)


async def _safe_ws_send(websocket: ServerConnection, payload: dict[str, object]) -> None:
    try:
        await websocket.send(json.dumps(payload))
    except Exception:
        pass


async def handle_websocket(websocket: ServerConnection):
    """Handle WebSocket connection for real-time transcription"""
    client_id = str(id(websocket))
    logger.info(f"New WebSocket connection from client: {client_id}")
    
    try:
        speech_service = SpeechService()
        speech_services[client_id] = speech_service
        
        # Initialize and wait for Oracle service to be ready
        success = await speech_service.initialize_websocket()
        if not success:
            logger.error("Failed to initialize Oracle service")
            await _safe_ws_send(websocket, ws_error("Failed to initialize Oracle speech service"))
            return

        await _safe_ws_send(websocket, ws_session_started(speech_service.listener.session_id))
            
        logger.info("Ready to process audio")
        
        last_transcript = ""

        try:
            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        sent = await speech_service.send_audio(message)
                        if sent:
                            transcript = speech_service.get_transcription()
                            if transcript and transcript != last_transcript:
                                last_transcript = transcript
                                await _safe_ws_send(websocket, ws_transcription(transcript=transcript, is_final=True))
                    else:
                        decoded_raw: object = json.loads(message)
                        if isinstance(decoded_raw, dict):
                            decoded = cast(dict[str, object], decoded_raw)
                            if decoded.get("type") != "close":
                                continue
                            logger.info(f"Client requested close: {client_id}")
                            await _safe_ws_send(websocket, ws_session_stopped())
                            break
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await _safe_ws_send(websocket, ws_error("Error processing websocket message"))
        except ConnectionClosed as e:
            logger.info(f"Client {client_id} disconnected: code={e.code}, reason={e.reason}")
            await _safe_ws_send(websocket, ws_connection_closed(code=e.code, message=e.reason or "Disconnected"))
        except ConnectionResetError:
            logger.info(f"Client {client_id} connection reset by peer")
        except Exception as e:
            logger.error(f"Unexpected websocket loop error for {client_id}: {e}")
            await _safe_ws_send(websocket, ws_error("Unexpected websocket server error"))
                
    finally:
        speech_service = speech_services.pop(client_id, None)
        if speech_service:
            await speech_service.close()
            logger.info(f"Cleaned up client: {client_id}")

async def main():
    async with websockets.serve(handle_websocket, "localhost", 5000, process_request=process_request):
        logger.info("WebSocket server started on ws://localhost:5000")
        logger.info("Health endpoint available at http://localhost:5000/health")
        logger.info("Readiness endpoint available at http://localhost:5000/ready")
        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            logger.info("Shutdown signal received; stopping websocket server")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
