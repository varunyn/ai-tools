from components.progress_display import EnhancedProgressMonitor


class _FakeStatusContainer:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _FakeProgressBar:
    def progress(self, value, text=""):
        return None


class _FakeStreamlit:
    def __init__(self):
        self.status_calls = []

    def status(self, *args, **kwargs):
        self.status_calls.append((args, kwargs))
        return _FakeStatusContainer()

    def progress(self, value, text=""):
        return _FakeProgressBar()

    def write(self, message):
        return None


def test_progress_monitor_uses_compact_status_container(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr("components.progress_display.st", fake_st)

    monitor = EnhancedProgressMonitor()
    monitor.start("Summarizing document")

    assert fake_st.status_calls == [
        (
            ("Summarizing document",),
            {"expanded": True, "state": "running", "type": "compact"},
        )
    ]
