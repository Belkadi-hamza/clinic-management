#!/usr/bin/env python3
"""
Alternative way to run the Cabinet Management application
This runs only the FastAPI server without the webview dependency
"""

import uvicorn
from pathlib import Path

def main():
    """Run the FastAPI server"""
    print("🏥 Starting Cabinet Management Server...")
    print("=" * 50)
    print("📡 Server will be available at: http://127.0.0.1:8000")
    print("🌐 Frontend will be available at: http://127.0.0.1:8000/app/index.html")
    print("🔧 API documentation at: http://127.0.0.1:8000/docs")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        uvicorn.run(
            "backend.app:app", 
            host="127.0.0.1", 
            port=8000, 
            reload=True,  # Enable auto-reload for development
            workers=1
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()
