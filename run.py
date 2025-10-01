#!/usr/bin/env python3
"""
Lilux App - Local Binance Trading WebApp
Launch script for development server
"""

import os
import sys
import uvicorn
from pathlib import Path

# Install python-dotenv if not available
try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing python-dotenv...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

def main():
    """Main entry point"""
    # Add current directory to Python path
    current_dir = Path(__file__).parent.absolute()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Create .env file if it doesn't exist
    env_file = current_dir / ".env"
    env_example = current_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("Please edit .env file with your configuration")
    
    # Load environment variables if .env exists
    if env_file.exists():
        load_dotenv(env_file)
    
    print("🚀 Starting Lilux Binance Local WebApp...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔐 Default credentials: admin / admin123")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run the server
        uvicorn.run(
            "lilux_app.backend.main:app",
            host="127.0.0.1",
            port=5000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Lilux App stopped")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()