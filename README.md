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

## Setup

1. Make sure you have Python 3.8+ installed
2. Run the setup script: ```python setup.py```
3. Start the application: ```python app.py```
4. Open your browser and navigate to `http://localhost:5000`

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
- `instance/` - Instance-specific files (database)

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