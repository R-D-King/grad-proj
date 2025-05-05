// Socket Module - Handles Socket.IO event listeners

// Set up Socket.IO event listeners
function setupSocketListeners(socket) {
    // Weather data updates (from database)
    socket.on('weather_update', function(data) {
        updateWeatherDisplay(data);
    });
    
    // Real-time sensor updates (more frequent)
    socket.on('sensor_update', function(data) {
        updateSensorDisplay(data);
    });
    
    // Irrigation system updates
    socket.on('pump_status', function(data) {
        const pumpStatus = document.getElementById('pump-status');
        pumpStatus.innerText = data.status === 'running' ? 'Running' : 'Stopped';
        pumpStatus.className = `badge ${data.status === 'running' ? 'bg-success' : 'bg-secondary'}`;
        
        if (data.status === 'running') {
            startRunningTimer();
        } else {
            stopRunningTimer();
        }
    });
    
    socket.on('water_level', function(data) {
        document.getElementById('water-level').innerText = data.level;
    });
    
    socket.on('preset_activated', function(data) {
        document.getElementById('current-preset').innerText = data.name;
    });
}

function updateWeatherDisplay(data) {
    // Update weather data from database (less frequent)
    if (data.temperature !== undefined) document.getElementById('temp').innerText = data.temperature;
    if (data.humidity !== undefined) document.getElementById('humidity').innerText = data.humidity;
    if (data.soil_moisture !== undefined) document.getElementById('soil-moisture').innerText = data.soil_moisture;
    if (data.pressure !== undefined) document.getElementById('pressure').innerText = data.pressure;
}

function updateSensorDisplay(data) {
    // Update sensor data in real-time (more frequent)
    if (data.temperature !== undefined) document.getElementById('temp').innerText = data.temperature;
    if (data.humidity !== undefined) document.getElementById('humidity').innerText = data.humidity;
    if (data.soil_moisture !== undefined) document.getElementById('soil-moisture').innerText = data.soil_moisture;
    if (data.water_level !== undefined) document.getElementById('water-level').innerText = data.water_level;
}

// Export function
window.setupSocketListeners = setupSocketListeners;