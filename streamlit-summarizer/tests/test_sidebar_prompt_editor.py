from pathlib import Path

from ui import sidebar


class _SessionState:
    def __init__(self, **values):
        object.__setattr__(self, "_values", values)

    def __contains__(self, key):
        return key in self._values

    def __getattr__(self, key):
        try:
            return self._values[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self._values[key] = value

    def __delattr__(self, key):
        del self._values[key]


class _Container:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _FakeStreamlit:
    def __init__(self):
        self.session_state = _SessionState(
            saved_prompts={},
            selected_prompt_name="Default Prompt",
            current_prompt="Summarize this text.",
            editing_prompt_name="",
        )
        self.text_area_calls = []
        self.text_input_calls = []
        self.button_calls = []
        self.container_calls = []

    def subheader(self, *args, **kwargs):
        return None

    def selectbox(self, *args, **kwargs):
        return None

    def expander(self, *args, **kwargs):
        return _Container()

    def text_area(self, *args, **kwargs):
        self.text_area_calls.append((args, kwargs))
        return None

    def dialog(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def divider(self):
        return None

    def text_input(self, *args, **kwargs):
        self.text_input_calls.append((args, kwargs))
        return None

    def container(self, *args, **kwargs):
        self.container_calls.append((args, kwargs))
        return _Container()

    def columns(self, count):
        return [_Container() for _ in range(count)]

    def button(self, *args, **kwargs):
        self.button_calls.append((args, kwargs))
        return False

    def error(self, *args, **kwargs):
        return None


def test_prompt_management_keeps_editor_out_of_sidebar(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(sidebar, "st", fake_st)

    sidebar._render_prompt_management()

    assert fake_st.text_area_calls == []
    assert fake_st.text_input_calls == []
    assert fake_st.button_calls == [
        (
            ("Edit prompt",),
            {
                "icon": ":material/edit:",
                "width": "stretch",
                "help": "Edit, save, or delete prompt templates.",
            },
        )
    ]


def test_prompt_dialog_uses_session_state_without_value_defaults(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(sidebar, "st", fake_st)

    sidebar._render_prompt_dialog_body()

    assert fake_st.session_state.prompt_editor == "Summarize this text."
    assert fake_st.session_state.new_prompt_name == ""
    assert fake_st.text_area_calls == [
        (
            ("Prompt Template",),
            {
                "key": "prompt_editor",
                "height": 200,
                "help": "Use {} as a placeholder for the text content",
                "on_change": sidebar.update_current_prompt_from_editor,
                "label_visibility": "visible",
            },
        )
    ]
    assert fake_st.text_input_calls == [
        (
            ("Prompt Name",),
            {
                "key": "new_prompt_name",
                "help": "Enter a name for your custom prompt",
            },
        )
    ]
    assert fake_st.container_calls == [
        ((), {"horizontal": True, "horizontal_alignment": "distribute"})
    ]
    assert fake_st.button_calls == [
        (
            ("Save prompt",),
            {
                "icon": ":material/save:",
                "on_click": sidebar.save_prompt,
                "type": "primary",
                "width": "stretch",
            },
        )
    ]


def test_sidebar_uses_current_width_and_button_group_patterns():
    source = Path("src/ui/sidebar.py").read_text()

    assert "use_container_width" not in source
    assert "st.columns(2)" not in source
    assert "st.container(horizontal=True" in source
    assert "@st.dialog" in source
    assert 'width="stretch"' in source
