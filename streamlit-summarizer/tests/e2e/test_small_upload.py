import os
from pathlib import Path

import pytest
from playwright.sync_api import Page

from .harness import get_free_port, run_streamlit_app
from .helpers import SUMMARY_HEADING_TEXT, generate_small_text_file, get_artifacts_dir


@pytest.mark.e2e
@pytest.mark.skipif(os.getenv("E2E_REAL_OCI") != "1", reason="Set E2E_REAL_OCI=1 to run E2E tests")
def test_small_upload_summarization(page: Page, tmp_path: Path) -> None:

    # Create minimal config.toml with required sections
    config_content = """
[app]
name = "Text Summarizer"
version = "1.0"
icon = "📝"

[models]
"Meta Llama 3.3 70B" = "meta.llama-3.3-70b-instruct"

[model_descriptions]
"Meta Llama 3.3 70B" = "Meta Llama 3.3 70B instruct model."

[prompt]
default = "Summarize the following content: {}"

[paths]
data_dir = "data"
logs_dir = "logs"

[processing]
max_saved_prompts = 5
max_file_size_mb = 200
chunk_size_chars = 6000
large_document_threshold = 8000
progress_update_interval = 0.5
monitor_thread_timeout = 1
"""
    config_file = tmp_path / "config.toml"
    _ = config_file.write_text(config_content.strip())

    # Create temp data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Generate small test file
    test_file_path = generate_small_text_file(str(tmp_path))

    # Get free port
    port = get_free_port()

    # Environment overrides
    env = {
        "APP_CONFIG_PATH": str(config_file.resolve()),
        "APP_DATA_DIR": str(data_dir.resolve()),
    }

    # Ensure artifacts directory exists
    evidence_dir = get_artifacts_dir()

    # Run Streamlit app
    with run_streamlit_app(port, env=env):
        # Navigate to the app
        _ = page.goto(f"http://127.0.0.1:{port}")

        # Upload the file using the file uploader
        file_input = page.get_by_test_id("stFileUploaderDropzone").locator("input[type=file]")
        file_input.set_input_files(test_file_path)

        # Wait for summary UI to render and summary box to be visible
        summary_heading = page.locator(f"text={SUMMARY_HEADING_TEXT}")
        summary_heading.wait_for(timeout=60000)
        # Wait for the Copy button which appears with the summary section
        page.get_by_role("button", name="📋 Copy to Clipboard").wait_for(timeout=60000)
        # Assert summary content is visible and non-empty
        summary_box = page.locator(".summary-box")
        summary_box.wait_for(timeout=60000)
        assert (summary_box.inner_text() or "").strip() != ""

        # Save screenshot
        screenshot_path = evidence_dir / "task-5-small-upload.png"
        _ = page.screenshot(path=str(screenshot_path))