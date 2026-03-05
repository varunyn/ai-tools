import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force reload environment variables
load_dotenv(override=True)

# Oracle Cloud Configuration
OCI_CONFIG = {
    "user": os.getenv("OCI_USER"),
    "key_file": os.getenv("OCI_KEY_FILE"),
    "fingerprint": os.getenv("OCI_FINGERPRINT"),
    "tenancy": os.getenv("OCI_TENANCY"),
    "region": os.getenv("OCI_REGION"),
    "compartment_id": os.getenv("OCI_COMPARTMENT_ID")
}

# Log configuration values (excluding sensitive data)
logger.info("OCI Configuration loaded:")
logger.info(f"  Region: {OCI_CONFIG['region']}")
logger.info(f"  Fingerprint: {OCI_CONFIG['fingerprint']}")
logger.info(f"  Key File exists: {os.path.exists(OCI_CONFIG['key_file'])}")
logger.info(f"  Compartment ID: {OCI_CONFIG['compartment_id']}")

# Validate configuration
for key, value in OCI_CONFIG.items():
    if value is None:
        logger.error(f"Missing required configuration: {key}")

# Audio Configuration
AUDIO_CONFIG = {
    "channels": 1,
    "sample_rate": 16000,
    "chunk_size": 1024,
    "format": "wav"
}

# API Configuration
API_CONFIG = {
    "transcription_language": "en-US",
    "audio_format": "WAV",
    "sample_rate": 16000,
    "channels": 1
} 
