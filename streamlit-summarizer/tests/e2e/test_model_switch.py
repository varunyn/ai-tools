import os
from pathlib import Path

import pytest
import re
from playwright.sync_api import Page

from .harness import get_free_port, run_streamlit_app
from .helpers import MODEL_LABEL, SUMMARY_HEADING_TEXT, generate_small_text_file, get_artifacts_dir


@pytest.mark.e2e
@pytest.mark.skipif(os.getenv("E2E_REAL_OCI") != "1", reason="Set E2E_REAL_OCI=1 to run E2E tests")
def test_model_switch_regenerates_summary(page: Page, tmp_path: Path) -> None:

    config_content = """
[app]
name = "Text Summarizer"
version = "1.0"
icon = "📝"

[models]
"OpenAI GPT-OSS 120b" = "openai.gpt-oss-120b"
"Google Gemini 2.5 Pro" = "google.gemini-2.5-pro"

[model_descriptions]
"OpenAI GPT-OSS 120b" = "OpenAI GPT-OSS 120b model."
"Google Gemini 2.5 Pro" = "Google Gemini 2.5 Pro model."

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

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    test_file_path = generate_small_text_file(str(tmp_path))

    port = get_free_port()

    env = {
        "APP_CONFIG_PATH": str(config_file.resolve()),
        "APP_DATA_DIR": str(data_dir.resolve()),
    }

    evidence_dir = get_artifacts_dir()

    with run_streamlit_app(port, env=env):
        _ = page.goto(f"http://127.0.0.1:{port}")

        file_input = page.get_by_test_id("stFileUploaderDropzone").locator("input[type=file]")
        file_input.set_input_files(test_file_path)

        summary_heading = page.locator(f"text={SUMMARY_HEADING_TEXT}")
        summary_heading.wait_for(timeout=60000)

        # Select the model combobox explicitly to avoid help button collisions
        model_select = page.get_by_role("combobox", name=re.compile(MODEL_LABEL, re.I))
        model_select.click()
        page.get_by_role("option", name="Google Gemini 2.5 Pro").click()

        summary_heading.wait_for(timeout=60000)

        sidebar = page.locator("[data-testid=stSidebar]")
        sidebar.get_by_test_id("stAlertContentInfo").get_by_text("Google Gemini 2.5 Pro").wait_for(timeout=60000)

        screenshot_path = evidence_dir / "task-6-model-switch.png"
        _ = page.screenshot(path=str(screenshot_path))