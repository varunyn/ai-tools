"""
Load application configuration from root-level config.toml and expose the same API
as before so existing imports continue to work.
"""
import os
import tomllib
from pathlib import Path
from typing import Any

# Project root: parent of src/ (this file lives in src/config/constants.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = Path(os.getenv('APP_CONFIG_PATH', _PROJECT_ROOT / "config.toml"))


def _load_config() -> dict[str, Any]:
    """Load and parse config.toml from project root."""
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {_CONFIG_PATH}. "
            "Create config.toml in the project root (see config.toml.example)."
        )
    with open(_CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


_config_cache: dict[str, Any] | None = None


def _get_config() -> dict[str, Any]:
    """Return cached config (load once)."""
    global _config_cache
    if _config_cache is None:
        _config_cache = _load_config()
    return _config_cache


# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------
def _app() -> dict[str, Any]:
    return _get_config().get("app", {})


APP_NAME = _app().get("name", "Text Summarizer")
APP_VERSION = _app().get("version", "1.0")
APP_ICON = _app().get("icon", "📝")

# ---------------------------------------------------------------------------
# Models: display name -> model_id, and descriptions
# ---------------------------------------------------------------------------
def _models() -> dict[str, Any]:
    return _get_config().get("models", {})


def _model_descriptions() -> dict[str, Any]:
    return _get_config().get("model_descriptions", {})


GENAI_MODELS = _models()
MODEL_OPTIONS = {name: GENAI_MODELS[name] for name in GENAI_MODELS}
MODEL_DESCRIPTIONS = _model_descriptions()

# ---------------------------------------------------------------------------
# Default prompt (placeholder: {})
# ---------------------------------------------------------------------------
def _prompt_default() -> str:
    raw = _get_config().get("prompt", {}).get("default", "")
    return raw.strip() if raw else "Summarize the following content: {}"


DEFAULT_PROMPT = _prompt_default()

# ---------------------------------------------------------------------------
# Paths and files
# ---------------------------------------------------------------------------
def _paths() -> dict[str, Any]:
    return _get_config().get("paths", {})


_DATA_DIR_RAW = os.getenv('APP_DATA_DIR', _paths().get("data_dir", "data"))
LOGS_DIR = _paths().get("logs_dir", "logs")

# Resolve data dir: use project root if relative
_data_dir = str(_PROJECT_ROOT / _DATA_DIR_RAW) if not os.path.isabs(_DATA_DIR_RAW) else _DATA_DIR_RAW
if not os.path.exists(_data_dir):
    try:
        os.makedirs(_data_dir, exist_ok=True)
    except OSError:
        _data_dir = str(_PROJECT_ROOT)
DATA_DIR = _data_dir

PROMPTS_FILE = os.path.join(DATA_DIR, "saved_prompts.json")
TEMP_DATA_FILE = os.path.join(DATA_DIR, "summarize_data.txt")
PROGRESS_FILE = os.path.join(DATA_DIR, "llama_progress.txt")

# ---------------------------------------------------------------------------
# Processing and limits
# ---------------------------------------------------------------------------
def _processing() -> dict[str, Any]:
    return _get_config().get("processing", {})


_proc = _processing()
MAX_SAVED_PROMPTS = int(_proc.get("max_saved_prompts", 5))
MAX_FILE_SIZE_MB = int(_proc.get("max_file_size_mb", 200))
CHUNK_SIZE_CHARS = int(_proc.get("chunk_size_chars", 6000))
LARGE_DOCUMENT_THRESHOLD = int(_proc.get("large_document_threshold", 8000))
PROGRESS_UPDATE_INTERVAL = float(_proc.get("progress_update_interval", 0.5))
MONITOR_THREAD_TIMEOUT = float(_proc.get("monitor_thread_timeout", 1))
