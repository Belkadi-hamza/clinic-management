import os
# Force pywebview to use Qt backend before importing webview
os.environ.setdefault("PYWEBVIEW_GUI", "qt")

import threading
import time
import uvicorn
from pathlib import Path
import webview
import requests


def run_api():
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False, workers=1)


def frontend_url() -> str:
    return "http://127.0.0.1:8000/app/index.html"


def check_server_ready(timeout=30):
    """Check if the server is ready to accept connections"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get("http://127.0.0.1:8000/", timeout=1)
            if response.status_code == 200:
                return True
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(0.5)
    return False


def on_window_loaded(window):
    """Callback when window finishes loading"""
    print("Window loaded successfully")


def on_window_closed(window):
    """Callback when window is closed"""
    print("Application window closed")


def start_app():
    """Function to check server and load appropriate page"""
    # Wait a bit for the window to be ready
    time.sleep(0.5)
    
    # Check if server is ready
    print("Checking if server is ready...")
    if check_server_ready(timeout=15):
        print("Server is ready, loading main application...")
        # Load the actual application
        window.load_url(frontend_url())
    else:
        print("Server failed to start, showing error page...")
        # Show connection error page
        window.load_url("http://127.0.0.1:8000/app/connection-refused.html")


if __name__ == "__main__":
    # Start the API server
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Give the server a moment to start
    time.sleep(1.5)
    
    # Create window with loading screen first
    window = webview.create_window(
        "Cabinet Management",
        "http://127.0.0.1:8000/app/index.html",
        width=1280, 
        height=800,
        resizable=True
    )
    
    # Start a thread to check server and load the app
    app_thread = threading.Thread(target=start_app, daemon=True)
    app_thread.start()
    
    # Start the webview (this is blocking)
    try:
        webview.start(debug=False)
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")