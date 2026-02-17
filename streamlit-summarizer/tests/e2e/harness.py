import contextlib
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def _wait_for_health(port: int, timeout: float = 60.0) -> None:
    url = f"http://127.0.0.1:{port}/_stcore/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError("Streamlit health check failed within timeout")


@contextlib.contextmanager
def run_streamlit_app(port: int, env: dict[str, str] | None = None, timeout: float = 60.0):
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    
    preexec_fn = os.setsid if os.name == 'posix' else None
    proc = subprocess.Popen(
        [sys.executable, '-m', 'streamlit', 'run', 'src/app.py',
         '--server.port', str(port), '--server.headless', 'true', '--server.address', '127.0.0.1'],
        env=env_vars,
        preexec_fn=preexec_fn
    )
    
    base_url = f"http://127.0.0.1:{port}"
    try:
        if proc.poll() is not None:
            raise RuntimeError("Streamlit process exited early")
        _wait_for_health(port, timeout)
        yield base_url
    finally:
        if os.name == 'posix':
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=10)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                proc.wait()
        else:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()