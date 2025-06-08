# Irrigation System

A web-based irrigation system with weather monitoring capabilities.

## Features

- Real-time weather monitoring
- Irrigation scheduling
- Preset management
- Report generation
- Pump control with duration tracking
- Customizable data reports with filtering options
- Temperature and humidity monitoring with DHT22 sensor
- Soil moisture monitoring with capacitive soil moisture sensor
- Light level monitoring with LDR sensor
- Rain detection with rain sensor
- Pressure and altitude monitoring with BMP180 sensor
- Periodic network status monitoring (IP address and SSID)

## Setup

### Standard Setup
1. Make sure you have Python 3.8+ installed
2. Run the setup script to create a virtual environment and install dependencies:
   ```python setup.py```
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
   - Light sensor (LDR) to MCP3008 ADC on channel 1
   - Rain sensor to MCP3008 ADC on channel 2
   - BMP180 pressure sensor to I2C bus
3. Run the setup script to create a virtual environment and install dependencies:
   ```python setup.py```
4. Activate the virtual environment: ```source venv/bin/activate```
5. Start the application: ```python app.py```
6. Access the web interface by navigating to your Raspberry Pi's IP address on port 5000

## Hardware Requirements

- Raspberry Pi (3B+ or 4 recommended)
- DHT22 temperature and humidity sensor
- Capacitive soil moisture sensor
- MCP3008 analog-to-digital converter (for soil moisture, LDR, and rain sensors)
- Light dependent resistor (LDR) for light level sensing
- Rain sensor with analog output
- BMP180 pressure and temperature sensor
- Relay module for pump control
- 16x2 LCD display (optional)

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
  - `pump.py` - Pump control logic
  - `soil_moisture.py` - Soil moisture sensor interface
  - `dht22.py` - DHT22 temperature and humidity sensor interface
  - `bmp180.py` - BMP180 pressure and temperature sensor interface
  - `ldr_aout.py` - Light dependent resistor sensor interface
  - `rain_aout.py` - Rain sensor interface
  - `lcd_16x2.py` - 16x2 LCD display interface
  - `sensor_controller.py` - Unified sensor management
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
- smbus (for I2C communication with BMP180)
- RPLCD (for LCD display)

## WebSocket Events

The application uses WebSockets for real-time updates:
- `weather_update` - Sent when new weather data is available
- `preset_activated` - Sent when an irrigation preset is activated
- `pump_status_change` - Sent when the pump status changes
- `sensor_update` - Sent when new sensor readings are available

## Known Issues

The following issues are currently being addressed:

1. Preset Management:
   - Cannot create or load irrigation presets
   - No way to select and activate a preset while deactivating others

2. Timer Functionality:
   - Running time counter may reset unexpectedly when browser refreshes
   - No persistent storage of pump running time across server restarts

3. Error Handling:
   - Insufficient error handling for API requests
   - No user feedback when server connections fail

4. UI/UX Issues:
   - Inconsistent responsive design on smaller screens
   - Limited accessibility features

5. Database Management:
   - No data pruning mechanism for old logs
   - Potential performance issues with large datasets

6. Security Concerns:
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
- `WeatherData` - Stores weather sensor readings (temperature, humidity, soil moisture, pressure, light, and rain)
- `Preset` - Stores irrigation configuration presets
- `Schedule` - Stores scheduled irrigation times
- `PumpLog` - Records pump start/stop events
- `IrrigationLog` - Records detailed irrigation events

### Sensor Calibration

The soil moisture sensor may need calibration for your specific soil type:
1. Place the sensor in completely dry soil and note the reading
2. Place the sensor in saturated soil and note the reading
3. Update the `DRY_VALUE` and `WET_VALUE` constants in `hardware/soil_moisture.py`

Similarly, the LDR sensor may need calibration for your lighting conditions:
1. Test the sensor in complete darkness and note the reading
2. Test the sensor in bright light and note the reading
3. Update the `min_value` and `max_value` parameters in `hardware/ldr_aout.py`

# Configuration

The application can be configured using JSON configuration files in the `config` directory and environment variables for key operational parameters.

## Environment Variables
- `UI_UPDATE_INTERVAL`: How often sensor readings are sent to the UI (in seconds, default: 1)
- `DB_UPDATE_INTERVAL`: How often sensor readings are stored in the database (in seconds, default: 60)
- `NETWORK_UPDATE_INTERVAL`: How often the network status is checked (in seconds, default: 60)
- `PORT`: The port to run the server on (default: 5000)
- `DEBUG`: Whether to run the server in debug mode (true/false, default: false)

## Logging Configuration

Sensor data logging is configured via the `config/logging.json` file. This allows you to enable or disable CSV logging, define where data is saved, and set validation limits.

```json
{
  "csv_enabled": true,
  "data_folder": "~/sensor_data",
  "log_interval": 60,
  "timestamp_format": "%Y-%m-%d %H:%M:%S",
  "validation_enabled": true,
  "validation_limits": { "...": "..." }
}
```
