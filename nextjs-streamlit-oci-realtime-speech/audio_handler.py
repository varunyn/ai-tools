import pyaudio
import wave
import numpy as np
import logging
from config import AUDIO_CONFIG

# Set up logging
logger = logging.getLogger(__name__)

class AudioHandler:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.frames = []
        
        # List available devices
        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        self.device_id = None
        
        # Find the default input device
        default_device = self.audio.get_default_input_device_info()
        logger.info(f"Default input device: {default_device['name']}")
        self.device_id = default_device['index']
        
        logger.info("AudioHandler initialized")
        
    def start_recording(self):
        """Start audio recording"""
        if self.stream is not None:
            self.stop_recording()
            
        logger.info(f"Starting audio recording with config: {AUDIO_CONFIG}")
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=AUDIO_CONFIG["channels"],
                rate=AUDIO_CONFIG["sample_rate"],
                input=True,
                input_device_index=self.device_id,
                frames_per_buffer=AUDIO_CONFIG["chunk_size"],
                stream_callback=None
            )
            self.is_recording = True
            self.frames = []
            logger.info("Audio recording started successfully")
        except Exception as e:
            logger.error(f"Error starting audio recording: {str(e)}")
            self.is_recording = False
        
    def stop_recording(self):
        """Stop audio recording"""
        logger.info("Stopping audio recording...")
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                logger.info("Audio stream closed successfully")
            except Exception as e:
                logger.error(f"Error stopping stream: {str(e)}")
            finally:
                self.stream = None
        
    def get_audio_chunk(self):
        """Get audio chunk from stream"""
        if not self.stream or not self.is_recording:
            logger.debug("Stream not active or not recording")
            return None
            
        try:
            # Read exactly one chunk
            logger.debug("Reading audio chunk...")
            data = self.stream.read(AUDIO_CONFIG["chunk_size"], exception_on_overflow=False)
            if data:
                # Verify data size
                expected_size = AUDIO_CONFIG["chunk_size"] * 2  # 2 bytes per sample for Int16
                if len(data) == expected_size:
                    # Convert to numpy array to check if there's actual sound
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume_norm = np.linalg.norm(audio_data) / len(audio_data)
                    logger.debug(f"Audio chunk captured. Size: {len(data)}, Volume: {volume_norm}")
                    
                    # Return all non-zero chunks
                    if np.any(audio_data != 0):
                        self.frames.append(data)
                        return data
                    else:
                        logger.debug("Chunk discarded - complete silence")
                else:
                    logger.warning(f"Incorrect chunk size: got {len(data)}, expected {expected_size}")
            else:
                logger.debug("No data read from stream")
            return None
        except Exception as e:
            if not isinstance(e, IOError) or e.errno != -9981:  # Ignore overflow errors
                logger.error(f"Error reading audio chunk: {str(e)}", exc_info=True)
            return None
        
    def save_audio(self, filename):
        """Save recorded audio to WAV file"""
        if not self.frames:
            logger.warning("No audio frames to save")
            return False
            
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(AUDIO_CONFIG["channels"])
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(AUDIO_CONFIG["sample_rate"])
                wf.writeframes(b''.join(self.frames))
            logger.info(f"Audio saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            return False
            
    def __del__(self):
        """Cleanup audio resources"""
        logger.info("Cleaning up audio resources")
        self.stop_recording()
        if self.audio:
            self.audio.terminate() 