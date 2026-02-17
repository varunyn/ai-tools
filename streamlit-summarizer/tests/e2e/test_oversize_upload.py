import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page

from .harness import get_free_port, run_streamlit_app
from .helpers import SUMMARY_HEADING_TEXT, generate_large_text_file, get_artifacts_dir  # pyright: ignore[reportMissingImports]


@pytest.mark.e2e
@pytest.mark.skipif(os.getenv("E2E_REAL_OCI") != "1", reason="Set E2E_REAL_OCI=1 to run E2E tests")
def test_oversize_upload_rejected(page: Page, tmp_path: Path) -> None:
    # Temp config with strict 1MB max file size
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
max_file_size_mb = 1
chunk_size_chars = 6000
large_document_threshold = 8000
progress_update_interval = 0.5
monitor_thread_timeout = 1
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content.strip())

    # Isolated data dir
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Generate ~2MB file to exceed 1MB limit
    test_file_path = generate_large_text_file(str(tmp_path), size_mb=2.0)

    # Free port + env overrides
    port = get_free_port()
    env = {
        "APP_CONFIG_PATH": str(config_file.resolve()),
        "APP_DATA_DIR": str(data_dir.resolve()),
    }

    # Artifacts directory
    evidence_dir = get_artifacts_dir()

    with run_streamlit_app(port, env=env):
        _ = page.goto(f"http://127.0.0.1:{port}")

        # Upload oversize file
        file_input = page.get_by_test_id("stFileUploaderDropzone").locator("input[type=file]")
        file_input.set_input_files(test_file_path)

        # Wait for app-level error to surface; assert meaningful text
        page.get_by_text(re.compile(r"file\s+is\s+too\s+large", re.IGNORECASE)).wait_for(timeout=30000)
        page.get_by_text(re.compile(r"max\s+allowed", re.IGNORECASE)).wait_for(timeout=30000)

        # Ensure summary section never appears
        summary_heading = page.locator(f"text={SUMMARY_HEADING_TEXT}")
        assert summary_heading.count() == 0

        # Screenshot evidence
        screenshot_path = evidence_dir / "task-8-oversize-rejected.png"
        _ = page.screenshot(path=str(screenshot_path))
