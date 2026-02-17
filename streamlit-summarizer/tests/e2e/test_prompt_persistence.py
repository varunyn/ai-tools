import os
import re
from pathlib import Path
import time

import pytest
from playwright.sync_api import Page

from .harness import get_free_port, run_streamlit_app
import importlib
_helpers = importlib.import_module("tests.e2e.helpers")
PROMPT_DROPDOWN_LABEL = getattr(_helpers, "PROMPT_DROPDOWN_LABEL")
PROMPT_NAME_TEXTBOX_LABEL = getattr(_helpers, "PROMPT_NAME_TEXTBOX_LABEL")
get_artifacts_dir = getattr(_helpers, "get_artifacts_dir")


@pytest.mark.e2e
@pytest.mark.skipif(os.getenv("E2E_REAL_OCI") != "1", reason="Set E2E_REAL_OCI=1 to run E2E tests")
def test_prompt_save_persists_across_reload(page: Page, tmp_path: Path) -> None:
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
    config_file.write_text(config_content.strip())

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    port = get_free_port()

    env = {
        "APP_CONFIG_PATH": str(config_file.resolve()),
        "APP_DATA_DIR": str(data_dir.resolve()),
    }

    evidence_dir = get_artifacts_dir()

    prompt_name = f"test-prompt-{int(time.time())}"

    with run_streamlit_app(port, env=env):
        _ = page.goto(f"http://127.0.0.1:{port}")

        prompt_name_input = page.get_by_role("textbox", name=PROMPT_NAME_TEXTBOX_LABEL)
        prompt_name_input.fill(prompt_name)

        save_button = page.get_by_role("button", name="💾 Save Prompt")
        save_button.click()

        page.get_by_text("saved").wait_for(timeout=5000)

        page.reload()

        prompt_dropdown = page.get_by_role("combobox", name=re.compile(PROMPT_DROPDOWN_LABEL))
        prompt_dropdown.click()

        prompt_option = page.get_by_role("option", name=prompt_name)
        prompt_option.wait_for(timeout=5000)

        screenshot_path = evidence_dir / "task-7-prompt-persists.png"
        _ = page.screenshot(path=str(screenshot_path))