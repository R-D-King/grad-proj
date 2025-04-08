import os
import sys
import subprocess
import platform

def is_raspberry_pi():
    """Check if the current system is a Raspberry Pi."""
    # Method 1: Check for Raspberry Pi model in /proc/cpuinfo
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Model') and 'Raspberry Pi' in line:
                    return True
    except:
        pass
    
    # Method 2: Check for ARM architecture on Linux
    return (platform.system() == 'Linux' and 
            platform.machine().startswith(('arm', 'aarch')))

def install_rpi_system_packages():
    """Install Raspberry Pi specific system packages using apt."""
    print("Installing Raspberry Pi system packages...")
    try:
        # Update package lists
        subprocess.check_call(["sudo", "apt", "update"])
        
        # Install pip first
        subprocess.check_call(["sudo", "apt", "install", "-y", "python3-pip"])
        
        # Install other required system packages
        rpi_packages = [
            "python3-rpi.gpio",
            "python3-spidev"
        ]
        
        subprocess.check_call(["sudo", "apt", "install", "-y"] + rpi_packages)
        print("Raspberry Pi system packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing system packages: {e}")
        return False

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
    
    # Detect if running on Raspberry Pi
    is_rpi = is_raspberry_pi()
    if is_rpi:
        print("Detected Raspberry Pi environment.")
        # Install system packages first
        if not install_rpi_system_packages():
            print("Warning: Some system packages could not be installed.")
        requirements_file = "requirements_rpi.txt"
    else:
        print("Detected standard environment.")
        requirements_file = "requirements.txt"
    
    # Install dependencies
    print(f"Installing dependencies from {requirements_file}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
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