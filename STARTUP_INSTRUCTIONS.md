
# Auto-start Python Web App on Raspberry Pi

Two methods to automatically start a Python web application in a virtual environment on Raspberry Pi boot, with network access (port 5000).

## Prerequisites
- Python virtual environment already created
- Web app is configured to run on port 5000
- Raspberry Pi with desktop environment (for Option 1)

## Option 1: Using `.bashrc` with `lxterminal` (Visible GUI Terminal)

Best for development/debugging when you need to see and interact with the terminal.

### Steps:

1. Install lxterminal:
   ```bash
   sudo apt update && sudo apt install lxterminal
   ```

2. Create startup script:
   ```bash
   nano ~/start_app.sh
   ```

3. Add this content:
   ```bash
   #!/bin/bash
   # Explicitly change to app directory
   cd /home/pi/Documents/grad-proj || exit

   # Activate virtual environment with full path
   source /home/pi/Documents/grad-proj/venv/bin/activate

   # Verify Python path
   echo "Using Python: $(which python3)"
   echo "Python path: $(python3 -c 'import sys; print(sys.path)')"

   # Run app with visible terminal
   lxterminal -e "bash -c 'source /home/pi/Documents/grad-proj/venv/bin/activate && python3 app.py --host=0.0.0.0 --port=5000; exec bash'"
   ```

4. Make executable:
   ```bash
   chmod +x ~/start_app.sh
   ```

5. Create autostart entry:
   ```bash
   mkdir -p ~/.config/autostart
   nano ~/.config/autostart/app.desktop
   ```

6. Add desktop entry:
   ```ini
   [Desktop Entry]
   Type=Application
   Name=My Python App
   Exec=/home/pi/start_app.sh
   Terminal=false
   ```

7. Reboot to test:
   ```bash
   sudo reboot
   ```

### How to Access/Stop:
- App runs in visible terminal window
- Access at `http://<pi-ip-address>:5000`
- Stop with Ctrl+C in terminal or close window

## Option 2: Using `screen` with crontab (Headless with Reattach Capability)

Best for headless operation when you might need to check logs occasionally.

### Steps:

1. Install screen:
   ```bash
   sudo apt update && sudo apt install screen
   ```

2. Create startup script:
   ```bash
   nano ~/start_app_screen.sh
   ```

3. Add this content:
   ```bash
   #!/bin/bash
   #!/bin/bash
   # Explicitly change to app directory
   cd /home/pi/Documents/grad-proj || exit

   # Activate virtual environment with full path
   source /home/pi/Documents/grad-proj/venv/bin/activate

   # Verify Python path
   echo "Using Python: $(which python3)" > /home/pi/app_start.log
   echo "Python path: $(python3 -c 'import sys; print(sys.path)')" >> /home/pi/app_start.log

   # Run app in screen session with logging
   screen -L -Logfile /home/pi/app_screen.log -dmS myapp \
   bash -c "source /home/pi/Documents/grad-proj/venv/bin/activate && \
   python3 app.py --host=0.0.0.0 --port=5000"
   ```

4. Make executable:
   ```bash
   chmod +x ~/start_app_screen.sh
   ```

5. Add to crontab:
   ```bash
   crontab -e
   ```

6. Add this line:
   ```
   @reboot /home/pi/start_app_screen.sh
   ```

7. Reboot to test:
   ```bash
   sudo reboot
   ```

### How to Access/Stop:
- View logs: `cat /home/pi/app_screen.log`
- Attach to session: `screen -r myapp`
- Detach: `Ctrl+A` then `D`
- Stop app: Attach then `Ctrl+C`
- Access at `http://<pi-ip-address>:5000`
