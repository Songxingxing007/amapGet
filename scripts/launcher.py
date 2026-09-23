"""Entry point for the packaged Windows build (and a convenience runner)."""

from __future__ import annotations

import os
import pathlib
import sys
import threading
import time
import webbrowser


def base_dir() -> pathlib.Path:
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys.executable).resolve().parent
    return pathlib.Path(__file__).resolve().parents[1]


def main() -> None:
    base = base_dir()
    os.environ.setdefault("DATA_DIR", str(base / "data"))
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    url = f"http://{host}:{port}"

    def open_later() -> None:
        time.sleep(3)
        webbrowser.open(url)

    threading.Thread(target=open_later, daemon=True).start()

    print(f"amap-poi-aoi is starting, data dir: {os.environ['DATA_DIR']}")
    print(f"open {url} in your browser (this window closing stops the server)")

    import uvicorn

    from app.main import app

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
