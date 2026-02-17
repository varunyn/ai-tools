import json
import os
import streamlit as st
from config.constants import PROMPTS_FILE
from utils.logger import get_logger

logger = get_logger(__name__)


@st.cache_data
def load_saved_prompts() -> dict[str, str]:
    """
    Load saved prompts from JSON file with caching.

    Cached via st.cache_data. Cache is cleared explicitly after save_prompts_to_file() writes, via load_saved_prompts.clear().

    Returns:
        Dictionary of saved prompts (name -> prompt template)
    """
    try:
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r') as f:
                prompts = json.load(f)
                logger.info(f"Loaded {len(prompts)} saved prompts")
                return prompts
        return {}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading saved prompts: {e}", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading saved prompts: {e}", exc_info=True)
        return {}


def save_prompts_to_file(prompts: dict[str, str]) -> None:
    """
    Save prompts to file and invalidate the cache.
    
    Args:
        prompts: Dictionary of prompts to save (name -> prompt template)
    """
    try:
        with open(PROMPTS_FILE, 'w') as f:
            json.dump(prompts, f, indent=2)
        # Invalidate the cache so the new prompts are loaded on next access
        load_saved_prompts.clear()
        logger.info(f"Saved {len(prompts)} prompts to file")
    except (IOError, OSError, PermissionError) as e:
        logger.error(f"Error saving prompts: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error saving prompts: {e}", exc_info=True)
        raise
