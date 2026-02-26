import os
from typing import List, Dict, Any, Optional, cast

from dotenv import load_dotenv
from oci_openai import OciOpenAI, OciUserPrincipalAuth

load_dotenv()

# OCI configuration (preserve env names/defaults exactly)
compartment_id: Optional[str] = os.getenv("OCI_COMPARTMENT_ID")
model_id: str = os.getenv("MODEL_ID", "meta.llama-4-scout-17b-16e-instruct")
oci_profile: str = os.getenv("OCI_CONFIG_PROFILE", "CHICAGO")
oci_config_file: str = os.getenv("OCI_CONFIG_FILE", "oci-config")

# Service endpoint: chat needs base + /actions/v1; conversations/responses need base WITHOUT /actions/v1.
_oci_genai_base: str = os.getenv(
    "OCI_GENERATIVE_AI_ENDPOINT",
    "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130",
).rstrip("/")


def _base_without_actions_v1(url: str) -> str:
    """Remove /actions/v1 from URL so conversations and responses hit the correct path."""
    u = url.rstrip("/")
    if u.endswith("/actions/v1"):
        return u[: -len("/actions/v1")].rstrip("/")
    return u


OCI_API_BASE_URL: str = _base_without_actions_v1(_oci_genai_base)
OCI_CHAT_BASE_URL: str = f"{_oci_genai_base}/actions/v1" if "/actions/v1" not in _oci_genai_base else _oci_genai_base

# Available models configuration (copied as-is)
AVAILABLE_MODELS: List[Dict[str, Any]] = [
    {
        "id": "meta.llama-4-maverick-17b-128e-instruct-fp8",
        "name": "Llama 4 Maverick",
        "chef": "Meta",
        "chefSlug": "llama",
        "providers": ["oci"],
    },
    {
        "id": "openai.gpt-oss-120b",
        "name": "GPT-OSS 120B",
        "chef": "OpenAI",
        "chefSlug": "openai",
        "providers": ["oci"],
    },
    {
        "id": "meta.llama-3.3-70b-instruct",
        "name": "Llama 3.3 70B",
        "chef": "Meta",
        "chefSlug": "llama",
        "providers": ["oci"],
    },
    {
        "id": "meta.llama-4-scout-17b-16e-instruct",
        "name": "Llama 4 Scout",
        "chef": "Meta",
        "chefSlug": "llama",
        "providers": ["oci"],
    },
    {
        "id": "google.gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "chef": "Google",
        "chefSlug": "google",
        "providers": ["oci"],
    },
    {
        "id": "xai.grok-4-fast-reasoning",
        "name": "Grok 4 Fast (Reasoning)",
        "chef": "xAI",
        "chefSlug": "xai",
        "providers": ["oci"],
    },
    {
        "id": "xai.grok-4-fast-non-reasoning",
        "name": "Grok 4 Fast",
        "chef": "xAI",
        "chefSlug": "xai",
        "providers": ["oci"],
    },
]

# Expand ~ in config file path if present
if oci_config_file.startswith("~"):
    oci_config_file = os.path.expanduser(oci_config_file)

# Two OCI OpenAI clients (different base URLs per OCI behavior):
# - chat.completions requires base + /actions/v1 (otherwise 404)
# - conversations.* and responses.* require base without /actions/v1 (otherwise 404)
try:
    client_chat = OciOpenAI(
        base_url=OCI_CHAT_BASE_URL,
        auth=OciUserPrincipalAuth(config_file=oci_config_file, profile_name=oci_profile),
        compartment_id=cast(Any, compartment_id),
    )
    client_api = OciOpenAI(
        base_url=OCI_API_BASE_URL,
        auth=OciUserPrincipalAuth(config_file=oci_config_file, profile_name=oci_profile),
        compartment_id=cast(Any, compartment_id),
    )
    # default for any code that only uses chat
    client = client_chat
    print("OCI OpenAI clients initialized (chat=actions/v1, api=base only)")
    print(f"Chat base URL: {client_chat.base_url}")
    print(f"API base URL (responses, conversations): {client_api.base_url}")
    print(f"Using OCI profile: {oci_profile} from {oci_config_file}")
except Exception as e:
    print(f"Failed to initialize OCI OpenAI client: {e}")
    client_chat = None
    client_api = None
    client = None
