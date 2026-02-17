"""
OCI Client utility with Streamlit caching support.

This module provides cached OCI client instances using st.cache_resource
to improve performance and prevent connection leaks.
"""
import os
import streamlit as st
import oci
import yaml
import logging
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


def get_oci_config(config_profile: str) -> dict:
    """
    Get OCI configuration from local file first, then fall back to system config.
    Supports both local Docker setup and system OCI configuration.
    
    Args:
        config_profile: The OCI config profile name to use
        
    Returns:
        OCI configuration dictionary
    """
    # Try local OCI config first (for Docker setup)
    local_config_path = '../config/oci-config'
    if os.path.exists(local_config_path):
        try:
            logger.debug(f"Loading OCI config from local path: {local_config_path}")
            return oci.config.from_file(local_config_path, config_profile)
        except Exception as e:
            logger.warning(f"Could not load local OCI config: {e}, falling back to system config")
    
    # Fall back to system OCI config
    system_config_path = '~/.oci/config'
    logger.debug(f"Loading OCI config from system path: {system_config_path}")
    return oci.config.from_file(system_config_path, config_profile)


def _cleanup_oci_client(client: oci.generative_ai_inference.GenerativeAiInferenceClient) -> None:
    """
    Cleanup function for OCI client when cache is released.
    
    Args:
        client: The OCI client instance to cleanup
    """
    try:
        # OCI clients don't have explicit close methods, but we can log cleanup
        # The client will be garbage collected
        pass
    except Exception as e:
        print(f"Warning: Error during OCI client cleanup: {e}")


@st.cache_data
def load_config() -> Dict[str, Any]:
    """
    Load YAML configuration file with caching.
    
    Searches for config.yaml in multiple locations:
    - /app/config.yaml (Docker)
    - ../config/config.yaml (local development)
    - config/config.yaml (alternative local)
    
    Returns:
        Dictionary containing configuration data
        
    Raises:
        FileNotFoundError: If config.yaml is not found in any expected location
    """
    config_paths = ['/app/config.yaml', '../config/config.yaml', 'config/config.yaml']
    config_file = None
    for path in config_paths:
        if os.path.exists(path):
            config_file = path
            break
    
    if not config_file:
        error_msg = (
            "config.yaml not found in any expected location. "
            "Please ensure config.yaml exists in one of: /app/config.yaml, ../config/config.yaml, or config/config.yaml"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.debug(f"Loading config from: {config_file}")
    with open(config_file, 'r') as file:
        config_data = yaml.safe_load(file)
        logger.debug("Config loaded successfully")
        return config_data


@st.cache_resource(on_release=_cleanup_oci_client)
def get_oci_client(config_profile: str, endpoint: str) -> oci.generative_ai_inference.GenerativeAiInferenceClient:
    """
    Get or create a cached OCI Generative AI Inference client.
    
    Uses st.cache_resource to cache the client instance across app reruns,
    preventing unnecessary connection recreation and improving performance.
    
    Args:
        config_profile: The OCI config profile name to use
        endpoint: The OCI service endpoint URL
        
    Returns:
        Cached OCI Generative AI Inference client instance
    """
    logger.info(f"Creating OCI client for endpoint: {endpoint}")
    config = get_oci_config(config_profile)
    client = oci.generative_ai_inference.GenerativeAiInferenceClient(
        config=config,
        service_endpoint=endpoint,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(10, 240)
    )
    logger.debug("OCI client created successfully")
    return client
