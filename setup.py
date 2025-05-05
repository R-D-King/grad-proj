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
            "python3-spidev",
            "python3-venv",
            "libgpiod2"  # Required for DHT sensor
        ]
        
        subprocess.check_call(["sudo", "apt", "install", "-y"] + rpi_packages)
        print("Raspberry Pi system packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing system packages: {e}")
        return False

# In the setup_environment function, update the pip installation part:

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
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError:
            print("Error: Failed to create virtual environment.")
            sys.exit(1)
    
    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_executable = os.path.join("venv", "Scripts", "pip")
        python_executable = os.path.join("venv", "Scripts", "python")
    else:
        pip_executable = os.path.join("venv", "bin", "pip")
        python_executable = os.path.join("venv", "bin", "python")
    
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
    
    # Check if requirements file exists
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found.")
        sys.exit(1)
    
    # Upgrade pip first to avoid issues
    print("Upgrading pip...")
    try:
        subprocess.check_call([pip_executable, "install", "--upgrade", "pip"])
        print("Pip upgraded successfully.")
    except subprocess.CalledProcessError:
        print("Warning: Failed to upgrade pip. Continuing with installation...")
    
    # Install dependencies in the virtual environment
    print(f"Installing dependencies from {requirements_file}...")
    try:
        # Use --no-cache-dir to avoid caching issues
        subprocess.check_call([pip_executable, "install", "--no-cache-dir", "-r", requirements_file])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to install dependencies: {e}")
        
        # Try an alternative approach if the first one fails
        print("Trying alternative installation method...")
        try:
            subprocess.check_call([python_executable, "-m", "pip", "install", "-r", requirements_file])
            print("Dependencies installed successfully with alternative method.")
        except subprocess.CalledProcessError:
            print("Error: Failed to install dependencies with alternative method.")
            sys.exit(1)
    
    # Create instance directory if it doesn't exist
    if not os.path.exists("instance"):
        os.makedirs("instance")
        print("Created instance directory.")
    
    print("Setup completed successfully!")
    print("\nTo run the application, activate the virtual environment and run app.py:")
    if platform.system() == "Windows":
        print("venv\\Scripts\\activate")
    else:
        print("source venv/bin/activate")
    print("python app.py")

if __name__ == "__main__":
    setup_environment()