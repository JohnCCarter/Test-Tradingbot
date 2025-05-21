import subprocess
import sys
import time
import os
import shutil

def start_servers():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Start Flask server
    flask_process = subprocess.Popen(
        [sys.executable, "src/dashboard.py"],
        cwd=current_dir
    )
    
    print("Starting Flask server...")
    # Wait for Flask to initialize
    time.sleep(3)
    
    # Check if npx is available
    npx_path = shutil.which('npx')
    if not npx_path:
        print("Error: npx not found. Please make sure Node.js is installed and in your PATH")
        flask_process.terminate()
        return
    
    # Start Next.js server using npx
    next_process = subprocess.Popen(
        [npx_path, "next", "dev"],
        cwd=current_dir
    )
    
    print("Starting Next.js server...")
    print("\nBoth servers are running!")
    print("Press Ctrl+C to stop both servers...")
    
    try:
        # Keep the script running
        flask_process.wait()
        next_process.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        flask_process.terminate()
        next_process.terminate()
        print("Servers stopped!")

if __name__ == "__main__":
    start_servers() 