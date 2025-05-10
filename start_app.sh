#!/bin/bash
# Wait for network
while ! ping -c 1 -W 1 google.com &> /dev/null; do
    sleep 1
done

# Explicitly change to app directory
cd /home/pi/Documents/grad-proj || exit

# Activate virtual environment with full path
source /home/pi/Documents/grad-proj/venv/bin/activate

# Verify Python path
echo "Using Python: $(which python3)"
echo "Python path: $(python3 -c 'import sys; print(sys.path)')"

# Run app with visible terminal
lxterminal -e "bash -c 'source /home/pi/Documents/grad-proj/venv/bin/activate && python3 app.py --host=0.0.0.0 --port=5000; exec bash'"