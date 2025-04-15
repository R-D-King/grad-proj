# Irrigation System

A web-based irrigation system with weather monitoring capabilities.

## Features

- Real-time weather monitoring
- Irrigation scheduling
- Preset management
- Report generation
- Pump control with duration tracking
- Water level monitoring
- Customizable data reports with filtering options
- Temperature and humidity monitoring with DHT22 sensor
- Soil moisture monitoring with capacitive soil moisture sensor

## Setup

### Standard Setup
1. Make sure you have Python 3.8+ installed
2. Run the setup script: ```python setup.py```
3. Activate the virtual environment:
   - Windows: ```venv\Scripts\activate```
   - Linux/Mac: ```source venv/bin/activate```
4. Start the application: ```python app.py```
5. Open your browser and navigate to `http://localhost:5000`

### Raspberry Pi Setup
1. Make sure you have Python 3.8+ installed on your Raspberry Pi
2. Connect the sensors:
   - DHT22 temperature/humidity sensor to GPIO pin 4
   - Soil moisture sensor to SPI interface (MCP3008 ADC on channel 0)
   - Water level sensor to GPIO pin 17
3. Run the setup script: ```python setup.py```
4. Activate the virtual environment: ```source venv/bin/activate```
5. Start the application: ```python app.py```
6. Access the web interface by navigating to your Raspberry Pi's IP address on port 5000

## Hardware Requirements

- Raspberry Pi (3B+ or 4 recommended)
- DHT22 temperature and humidity sensor
- Capacitive soil moisture sensor
- MCP3008 analog-to-digital converter (for soil moisture sensor)
- Water level sensor
- Relay module for pump control

## Project Structure

- `app.py` - Main application file
- `shared/` - Shared utilities and components
  - `database.py` - Database configuration
  - `config.py` - Application configuration
  - `socketio.py` - WebSocket setup
  - `utils.py` - Utility functions
- `irrigation/` - Irrigation system functionality
  - `controllers.py` - Pump and water level control
  - `models.py` - Database models for irrigation
  - `routes.py` - API endpoints for irrigation
- `weather/` - Weather monitoring functionality
  - `controllers.py` - Weather data processing
  - `models.py` - Database models for weather data
  - `routes.py` - API endpoints for weather
- `reports/` - Report generation functionality
  - `controllers.py` - Report generation logic
  - `routes.py` - API endpoints for reports
- `static/` - Static files (CSS, JavaScript)
  - `js/` - JavaScript files
  - `css/` - CSS stylesheets
- `templates/` - HTML templates
  - `index.html` - Main application interface
- `hardware/` - Hardware interface modules
  - `relay.py` - Relay control for pump
  - `water_level.py` - Water level sensor interface
  - `pump.py` - Pump control logic
  - `soil_moisture.py` - Soil moisture sensor interface
  - `dht22.py` - DHT22 temperature and humidity sensor interface
  - `sensor_controller.py` - Unified sensor management
  - `sensor_simulation.py` - Sensor simulation for development
- `instance/` - Instance-specific files (database)
- `venv/` - Virtual environment (created by setup.py)

## API Endpoints

### Irrigation

- `GET /api/irrigation/status` - Get current irrigation system status
- `GET /api/irrigation/presets` - Get all presets
- `GET /api/irrigation/preset/<id>` - Get preset details
- `POST /api/irrigation/preset` - Create a new preset
- `POST /api/irrigation/preset/<id>/activate` - Activate a preset
- `DELETE /api/irrigation/preset/<id>` - Delete a preset
- `POST /api/irrigation/schedule` - Create a new schedule
- `PUT /api/irrigation/schedule/<id>` - Update a schedule
- `DELETE /api/irrigation/schedule/<id>` - Delete a schedule
- `POST /api/irrigation/pump/start` - Start the pump
- `POST /api/irrigation/pump/stop` - Stop the pump
- `GET /api/irrigation/pump/duration` - Get current pump duration

### Weather

- `GET /api/weather/current` - Get current weather data
- `POST /api/weather/update` - Update weather data

### Reports

- `POST /api/reports/generate` - Generate a report
- `GET /api/reports/download` - Download a report as CSV

## Dependencies

The project requires the following Python packages:
- Flask 2.3.3
- Flask-SQLAlchemy 3.1.1
- Flask-SocketIO 5.3.6
- python-socketio 5.10.0
- python-engineio 4.8.0
- eventlet 0.33.3
- Werkzeug 2.3.7
- Jinja2 3.1.2
- SQLAlchemy 2.0.21
- python-dateutil 2.8.2

For Raspberry Pi, additional packages are required:
- RPi.GPIO (for GPIO control)
- spidev (for SPI communication)
- adafruit-circuitpython-dht (for DHT22 sensor)

## WebSocket Events

The application uses WebSockets for real-time updates:
- `weather_update` - Sent when new weather data is available
- `preset_activated` - Sent when an irrigation preset is activated
- `pump_status_change` - Sent when the pump status changes

## Resolved Issues

The following issues have been fixed:

1. Pump Control:
   - ✅ Fixed pump duration tracking and display
   - ✅ Resolved type mismatch error when stopping the pump
   - ✅ Pump duration now correctly recorded in the database

2. Report Generation:
   - ✅ Report options now properly filter displayed data
   - ✅ Clear button for reports is now functioning

3. Date Selection:
   - ✅ Default dates for reports now display properly

4. Report Filtering:
   - ✅ Report data now only shows selected columns
   - ✅ Downloaded CSV reports only include selected data columns

5. UI Display:
   - ✅ Fixed water level display showing duplicate percentage signs
   - ✅ Running time counter now displays integer values without decimal places

## Known Issues

The following issues are currently being addressed:

1. Preset Management:
   - Cannot create or load irrigation presets
   - No way to select and activate a preset while deactivating others

## Potential Issues

These are additional concerns that may need attention:

1. Timer Functionality:
   - Running time counter may reset unexpectedly when browser refreshes
   - No persistent storage of pump running time across server restarts

2. Error Handling:
   - Insufficient error handling for API requests
   - No user feedback when server connections fail

3. UI/UX Issues:
   - Inconsistent responsive design on smaller screens
   - Limited accessibility features

4. Database Management:
   - No data pruning mechanism for old logs
   - Potential performance issues with large datasets

5. Security Concerns:
   - No authentication system for controlling pump
   - API endpoints lack proper validation

## Development

### Adding New Features

1. Create appropriate models in the relevant module
2. Add controller functions to handle business logic
3. Create routes to expose API endpoints
4. Update the frontend JavaScript to interact with new endpoints
5. Add WebSocket events if real-time updates are needed

### Database Schema

The application uses SQLAlchemy with the following main models:
- `WeatherData` - Stores weather sensor readings
- `Preset` - Stores irrigation configuration presets
- `Schedule` - Stores scheduled irrigation times
- `PumpLog` - Records pump start/stop events
- `IrrigationLog` - Records detailed irrigation events

### Sensor Calibration

The soil moisture sensor may need calibration for your specific soil type:
1. Place the sensor in completely dry soil and note the reading
2. Place the sensor in saturated soil and note the reading
3. Update the `DRY_VALUE` and `WET_VALUE` constants in `hardware/soil_moisture.py`

# Configuration

The application can be configured using JSON configuration files in the `config` directory and environment variables for key operational parameters.

## Environment Variables

The following environment variables can be used to override configuration settings:

- `UI_UPDATE_INTERVAL`: How often sensor readings are sent to the UI (in seconds, default: 1)
- `DB_UPDATE_INTERVAL`: How often sensor readings are stored in the database (in seconds, default: 60)
- `SENSOR_SIMULATION`: Whether to use simulated sensors instead of hardware (true/false, default: false)
- `PORT`: The port to run the server on (default: 5000)
- `DEBUG`: Whether to run the server in debug mode (true/false, default: false)
- `DATA_RETENTION_DAYS`: How many days of data to keep before pruning (default: 30)
- `DATA_RETENTION_ENABLED`: Whether to enable automatic data pruning (true/false, default: true)

Example of setting configuration on Windows:
```cmd
set UI_UPDATE_INTERVAL=2
set DB_UPDATE_INTERVAL=120
set SENSOR_SIMULATION=true

python app.py
```

Example of setting configuration on Linux/Mac:
```bash
export UI_UPDATE_INTERVAL=2
export DB_UPDATE_INTERVAL=120

python app.py
```