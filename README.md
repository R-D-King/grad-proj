# Irrigation System

A web-based irrigation system with weather monitoring capabilities.

## Features

- Real-time weather monitoring
- Irrigation scheduling
- Preset management
- Report generation

## Setup

1. Make sure you have Python 3.8+ installed
2. Run the setup script: ```python setup.py```
3. Start the application: ```python app.py```
4. Open your browser and navigate to `http://localhost:5000`

## Project Structure

- `app.py` - Main application file
- `shared/` - Shared utilities and components
- `irrigation/` - Irrigation system functionality
- `weather/` - Weather monitoring functionality
- `static/` - Static files (CSS, JavaScript)
- `templates/` - HTML templates
- `instance/` - Instance-specific files (database)

## API Endpoints

### Irrigation

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

### Weather

- `GET /api/weather/current` - Get current weather data
- `POST /api/weather/update` - Update weather data

### Reports

- `POST /api/reports/generate` - Generate a report
- `GET /api/reports/download` - Download a report as CSV