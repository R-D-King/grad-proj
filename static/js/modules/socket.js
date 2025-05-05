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

// Add this function to update sensor status indicators
function updateSensorStatus(data) {
    if (data.sensor_status) {
        // Update DHT sensor status
        const dhtStatus = document.getElementById('dht-status');
        if (dhtStatus) {
            if (data.sensor_status.dht_simulated) {
                dhtStatus.className = 'badge bg-warning';
                dhtStatus.innerText = 'Simulated';
            } else {
                dhtStatus.className = 'badge bg-success';
                dhtStatus.innerText = 'Connected';
            }
        }
        
        // Update soil moisture sensor status
        const soilStatus = document.getElementById('soil-status');
        if (soilStatus) {
            if (data.sensor_status.soil_simulated) {
                soilStatus.className = 'badge bg-warning';
                soilStatus.innerText = 'Simulated';
            } else {
                soilStatus.className = 'badge bg-success';
                soilStatus.innerText = 'Connected';
            }
        }
        
        // Water level is always simulated for now
        const waterStatus = document.getElementById('water-status');
        if (waterStatus) {
            waterStatus.className = 'badge bg-warning';
            waterStatus.innerText = 'Simulated';
        }
    }
}

// Add this to your socket connection setup
socket.on('sensor_status', function(data) {
    updateSensorStatus(data);
});

// Add this to your initialization function
function initializeSocket() {
    // Request sensor status on connection
    socket.on('connect', function() {
        socket.emit('get_sensor_status');
    });
    
    socket.on('water_level', function(data) {
        document.getElementById('water-level').innerText = data.level;
    });
    
    socket.on('preset_activated', function(data) {
        document.getElementById('current-preset').innerText = data.name;
    });
}

// Export function
window.setupSocketListeners = setupSocketListeners;