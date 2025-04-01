// Socket Module - Handles Socket.IO event listeners

// Set up Socket.IO event listeners
function setupSocketListeners(socket) {
    // Weather data updates
    socket.on('weather_update', function(data) {
        document.getElementById('temp').innerText = data.temperature;
        document.getElementById('humidity').innerText = data.humidity;
        document.getElementById('soil-moisture').innerText = data.soil_moisture;
        document.getElementById('wind-speed').innerText = data.wind_speed;
        document.getElementById('pressure').innerText = data.pressure;
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

// Export function
window.setupSocketListeners = setupSocketListeners;