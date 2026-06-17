import tomllib
from pathlib import Path


def test_streamlit_toolbar_uses_minimal_mode() -> None:
    config = tomllib.loads(Path(".streamlit/config.toml").read_text())

    assert config["client"]["toolbarMode"] == "minimal"


def test_app_does_not_inject_custom_css() -> None:
    app_source = Path("src/app.py").read_text()

    assert "CUSTOM_CSS" not in app_source
    assert "st.html(" not in app_source


def test_source_uses_native_summary_container() -> None:
    main_content_source = Path("src/ui/main_content.py").read_text()

    assert "unsafe_allow_html" not in main_content_source
    assert "summary-box" not in main_content_source
    assert "st.container(border=True)" in main_content_source
