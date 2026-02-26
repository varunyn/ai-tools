#!/usr/bin/env python3
"""
Loads .env and prints the exact response or exception from the OCI client.
"""
import os
import sys

# Load .env from backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from dotenv import load_dotenv
load_dotenv()

from oci_openai import OciOpenAI, OciUserPrincipalAuth


def _base_without_actions_v1(url: str) -> str:
    u = url.rstrip("/")
    if u.endswith("/actions/v1"):
        return u[: -len("/actions/v1")].rstrip("/")
    return u


def main() -> None:
    compartment_id = os.getenv("OCI_COMPARTMENT_ID")
    oci_profile = os.getenv("OCI_CONFIG_PROFILE", "CHICAGO")
    oci_config_file = os.getenv("OCI_CONFIG_FILE", "oci-config")
    base_from_env = os.getenv(
        "OCI_GENERATIVE_AI_ENDPOINT",
        "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130",
    ).rstrip("/")

    # Conversations API requires /open/v1 on the base URL
    api_base_url = base_from_env if base_from_env.endswith("/open/v1") else f"{base_from_env}/openai/v1/"

    if oci_config_file.startswith("~"):
        oci_config_file = os.path.expanduser(oci_config_file)

    print("Config:")
    print(f"  OCI_GENERATIVE_AI_ENDPOINT (from env): {base_from_env}")
    print(f"  API base URL (for conversations):      {api_base_url}")
    print(f"  OCI_CONFIG_FILE:                       {oci_config_file}")
    print(f"  OCI_CONFIG_PROFILE:                    {oci_profile}")
    conversation_store_id = os.getenv("OCI_CONVERSATION_STORE_ID")
    print(f"  OCI_COMPARTMENT_ID:                    {compartment_id or '(not set)'}")
    print(f"  OCI_CONVERSATION_STORE_ID:             {conversation_store_id or '(not set)'}")
    print()

    if not compartment_id:
        print("ERROR: OCI_COMPARTMENT_ID not set in .env")
        sys.exit(1)

    if not conversation_store_id:
        print("ERROR: OCI_CONVERSATION_STORE_ID not set in .env")
        print("       Add OCI_CONVERSATION_STORE_ID=<your-store-id> to .env for conversations API (opc-conversation-store-id header).")
        sys.exit(1)

    client = OciOpenAI(
        base_url=api_base_url,
        auth=OciUserPrincipalAuth(
            config_file=oci_config_file,
            profile_name=oci_profile,
        ),
        region="CHICAGO",
        compartment_id=compartment_id,
    )

    payload = {
        "metadata": {"topic": "test"},
        "items": [{"type": "message", "role": "user", "content": "Hello!"}],
    }
    if conversation_store_id:
        payload["extra_headers"] = {"opc-conversation-store-id": conversation_store_id}
    print("Calling client.conversations.create(...)")
    print(f"  payload: {payload}")
    print()

    try:
        conversation = client.conversations.create(**payload)
        print("Response (success):")
        print(f"  type: {type(conversation)}")
        if hasattr(conversation, "model_dump"):
            print(f"  model_dump(): {conversation.model_dump()}")
        elif hasattr(conversation, "__dict__"):
            print(f"  __dict__: {conversation.__dict__}")
        else:
            print(f"  repr: {conversation!r}")
    except Exception as e:
        print("Response (exception):")
        print(f"  type: {type(e).__name__}")
        print(f"  message: {e}")
        if hasattr(e, "response") and e.response is not None:
            status = getattr(e.response, "status_code", "N/A")
            print(f"  response.status_code: {status}")
            print(f"  response body:        {getattr(e.response, 'text', getattr(e.response, 'body', 'N/A'))}")
            if status == 404:
                print("  --> 404: endpoint may not support Conversations API.")
            if status == 400 and "opc-conversation-store-id" in str(e).lower():
                print("  --> Set OCI_CONVERSATION_STORE_ID in .env and re-run.")
        import traceback
        print()
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
