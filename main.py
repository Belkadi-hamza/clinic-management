import os
# Force pywebview to use Qt backend before importing webview
os.environ.setdefault("PYWEBVIEW_GUI", "qt")

import threading
import time
import uvicorn
from pathlib import Path
import webview


def run_api():
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False, workers=1)


def frontend_url() -> str:
    return "http://127.0.0.1:8000/app/index.html"


if __name__ == "__main__":
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    time.sleep(1.0)

    webview.create_window("Cabinet Management", frontend_url(), width=1280, height=800)
    webview.start()