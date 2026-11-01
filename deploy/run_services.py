import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from threading import Event


ROOT = Path(__file__).resolve().parents[1]
stopping = Event()


def request_shutdown(signum: int, frame: object) -> None:
    stopping.set()


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main() -> int:
    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)

    simulator_env = os.environ.copy()
    simulator_env["PYTHONPATH"] = str(ROOT / "simulator")
    simulator_env["SIMULATOR_PORT"] = "8001"

    api_env = os.environ.copy()
    api_env["PYTHONPATH"] = str(ROOT / "api")
    api_env["SIMULATOR_URL"] = "http://127.0.0.1:8001"
    api_env["API_HOST"] = "0.0.0.0"
    api_env["API_PORT"] = os.environ.get("PORT", "10000")

    simulator = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=ROOT / "simulator",
        env=simulator_env,
    )
    api = None

    try:
        api = subprocess.Popen(
            [sys.executable, "-m", "app.main"],
            cwd=ROOT / "api",
            env=api_env,
        )

        while not stopping.wait(1):
            if api.poll() is not None:
                return api.returncode
            if simulator.poll() is not None:
                print(
                    f"Simulator exited unexpectedly with status {simulator.returncode}.",
                    file=sys.stderr,
                    flush=True,
                )
                return 1
        return 0
    finally:
        if api is not None:
            stop_process(api)
        stop_process(simulator)


if __name__ == "__main__":
    raise SystemExit(main())
