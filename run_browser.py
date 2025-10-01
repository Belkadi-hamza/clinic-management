#!/usr/bin/env python3
"""
Browser-based launcher for Cabinet Management
This starts the server and opens it in the default browser
"""

import threading
import time
import webbrowser
import uvicorn
from pathlib import Path

def run_server():
    """Run the FastAPI server in a separate thread"""
    uvicorn.run(
        "backend.app:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=False,  # Disable reload for production
        workers=1,
        log_level="info"
    )

def main():
    """Start server and open browser"""
    print("🏥 Starting Cabinet Management Application...")
    print("=" * 60)
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("⏳ Starting server...")
    time.sleep(3)
    
    # Open browser
    url = "http://127.0.0.1:8000/app/index.html"
    print(f"🌐 Opening browser at: {url}")
    print("=" * 60)
    print("💡 Application is now running!")
    print("   - Frontend: http://127.0.0.1:8000/app/index.html")
    print("   - Login: http://127.0.0.1:8000/app/login.html")
    print("   - API Docs: http://127.0.0.1:8000/docs")
    print("   - Health Check: http://127.0.0.1:8000/health")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        webbrowser.open(url)
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
