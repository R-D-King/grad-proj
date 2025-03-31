import os
import sys
import subprocess

def setup_environment():
    """Set up the Python environment for the project."""
    print("Setting up the environment...")
    
    # Check if Python is installed
    try:
        python_version = subprocess.check_output(["python", "--version"]).decode().strip()
        print(f"Using {python_version}")
    except:
        print("Error: Python is not installed or not in PATH.")
        sys.exit(1)
    
    # Install dependencies
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("Error: Failed to install dependencies.")
        sys.exit(1)
    
    # Create instance directory if it doesn't exist
    if not os.path.exists("instance"):
        os.makedirs("instance")
        print("Created instance directory.")
    
    print("Setup completed successfully!")
    print("\nTo run the application, use:")
    print("python app.py")

if __name__ == "__main__":
    setup_environment()