import os
from pathlib import Path


def get_artifacts_dir() -> Path:
    """Get the directory for E2E test artifacts (screenshots, etc.).

    Defaults to 'test-results/e2e' relative to repo root.
    Can be overridden via E2E_ARTIFACTS_DIR env var (absolute or relative path).

    Creates the directory if it doesn't exist.
    """
    dir_path = os.getenv("E2E_ARTIFACTS_DIR", "test-results/e2e")
    artifacts_dir = Path(dir_path)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir


def generate_small_text_file(dir_path: str) -> str:
    content = "This is a small test file with minimal content for basic testing purposes."
    file_path = os.path.join(dir_path, "small.txt")
    with open(file_path, "w") as f:
        f.write(content)
    return file_path


def generate_large_text_file(dir_path: str, size_mb: float) -> str:
    size_bytes = int(size_mb * 1024 * 1024)
    chunk = "A" * 1024
    file_path = os.path.join(dir_path, "large.txt")
    with open(file_path, "w") as f:
        written = 0
        while written < size_bytes:
            remaining = size_bytes - written
            if remaining >= 1024:
                f.write(chunk)
                written += 1024
            else:
                f.write("A" * remaining)
                written += remaining
    return file_path


FILE_UPLOADER_LABEL = "Choose a text file"
MODEL_LABEL = "AI Model"
PROMPT_DROPDOWN_LABEL = "Select a Prompt"
PROMPT_NAME_TEXTBOX_LABEL = "Prompt Name"
SUMMARY_HEADING_TEXT = "📄 Generated Summary"