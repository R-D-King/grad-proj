document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO connection
    const socket = io();
    
    // Initialize UI components
    initializeUI();
    
    // Set up Socket.IO event listeners
    setupSocketListeners(socket);
    
    // Set up UI event listeners
    setupEventListeners();
    
    // Load presets on page load
    loadPresets();
});

// Initialize Bootstrap modals
function initializeUI() {
    window.addPresetModal = new bootstrap.Modal(document.getElementById('addPresetModal'));
    window.addScheduleModal = new bootstrap.Modal(document.getElementById('addScheduleModal'));
    window.editScheduleModal = new bootstrap.Modal(document.getElementById('editScheduleModal'));
}

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

// Set up UI event listeners
function setupEventListeners() {
    // Manual pump control
    document.getElementById('manual-on-btn').addEventListener('click', function() {
        if (confirm('Are you sure you want to start the pump?')) {
            fetch('/api/irrigation/pump/start', { method: 'POST' });
        }
    });
    
    document.getElementById('manual-off-btn').addEventListener('click', function() {
        if (confirm('Are you sure you want to stop the pump?')) {
            fetch('/api/irrigation/pump/stop', { method: 'POST' });
        }
    });
    
    // Preset management
    document.getElementById('addPresetBtn').addEventListener('click', () => addPresetModal.show());
    document.getElementById('savePresetBtn').addEventListener('click', saveNewPreset);
    
    // Schedule management
    document.getElementById('addScheduleBtn').addEventListener('click', () => addScheduleModal.show());
    document.getElementById('saveScheduleBtn').addEventListener('click', saveNewSchedule);
    document.getElementById('updateScheduleBtn').addEventListener('click', updateSchedule);
    
    // Report buttons
    document.getElementById('generateReportBtn').addEventListener('click', generateReport);
    document.getElementById('downloadReportBtn').addEventListener('click', downloadReport);
    document.getElementById('clearReportBtn').addEventListener('click', clearReports);
    document.getElementById('report-type').addEventListener('change', toggleReportOptions);
}

// Server time functionality
document.addEventListener('DOMContentLoaded', function() {
    // Update time display every second, but only fetch from server every 30 seconds
    let serverTimeOffset = 0;
    let lastFetchTime = 0;
    
    function updateTimeDisplay() {
        const timeDisplay = document.getElementById('server-time-display');
        if (!timeDisplay) return;
        
        const now = new Date();
        const currentTime = now.getTime();
        
        // Only fetch from server every 30 seconds to reduce requests
        if (currentTime - lastFetchTime > 30000) {
            fetch('/api/server-time/display')
                .then(response => response.json())
                .then(data => {
                    timeDisplay.textContent = data.formatted_time;
                    timeDisplay.style.color = '';
                    lastFetchTime = currentTime;
                })
                .catch(error => {
                    console.error('Error getting server time:', error);
                    timeDisplay.textContent = 'Server offline';
                    timeDisplay.style.color = 'red';
                });
        } else {
            // Update time locally between server fetches
            const hours = now.getHours().toString().padStart(2, '0');
            const minutes = now.getMinutes().toString().padStart(2, '0');
            const seconds = now.getSeconds().toString().padStart(2, '0');
            timeDisplay.textContent = `${hours}:${minutes}:${seconds}`;
        }
    }
    
    // Update time display every second
    setInterval(updateTimeDisplay, 1000);
    
    // Initial update
    updateTimeDisplay();
});

// Function to check schedule time - fully server-side implementation
function checkScheduleTime(scheduleId) {
    return fetch(`/api/schedule/${scheduleId}/should-run`)
        .then(response => response.json())
        .then(data => {
            return data.should_run;
        })
        .catch(error => {
            console.error('Error checking schedule time:', error);
            return false;
        });
}

// Timer functions for pump running time
let runningInterval;
let runningTime = 0;

function startRunningTimer() {
    runningTime = 0;
    document.getElementById('running-time').innerText = runningTime;
    runningInterval = setInterval(function() {
        runningTime++;
        document.getElementById('running-time').innerText = runningTime;
    }, 1000);
}

function stopRunningTimer() {
    clearInterval(runningInterval);
    runningTime = 0;
    document.getElementById('running-time').innerText = runningTime;
}

// Report functions - removed setDefaultDates function

function generateReport() {
    const reportType = document.getElementById('report-type').value;
    
    // Get dates from input fields
    let startDate = document.getElementById('report-start-date').value;
    let endDate = document.getElementById('report-end-date').value;
    
    // Fix the options collection to match the actual checkbox IDs
    const options = {};
    if (reportType === 'weather') {
        options.temperature = document.getElementById('weather-temperature').checked;
        options.humidity = document.getElementById('weather-humidity').checked;
        options.soil_moisture = document.getElementById('weather-soil-moisture').checked;
        options.wind_speed = document.getElementById('weather-wind-speed').checked;
        options.pressure = document.getElementById('weather-pressure').checked;
    } else {
        options.pump_status = document.getElementById('irrigation-pump-status').checked;
        options.water_level = document.getElementById('irrigation-water-level').checked;
        options.duration = document.getElementById('irrigation-duration').checked;
    }
    
    fetch('/api/reports/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            report_type: reportType,
            start_date: startDate,
            end_date: endDate,
            options: options
        })
    })
    .then(response => response.json())
    .then(data => {
        displayReport(data, reportType);
    })
    .catch(error => console.error('Error generating report:', error));
}

function displayReport(data, reportType) {
    const reportDisplay = document.getElementById('report-display');
    console.log("Report data:", data); // Debug log

    if (!data || data.length === 0) {
        reportDisplay.innerHTML = '<p class="text-center text-muted">No data available for the selected period</p>';
        return;
    }

    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Date/Time</th>
    `;

    // Add headers based on report type
    if (reportType === 'weather') {
        if (document.getElementById('weather-temperature').checked) tableHTML += '<th>Temperature (°C)</th>';
        if (document.getElementById('weather-humidity').checked) tableHTML += '<th>Humidity (%)</th>';
        if (document.getElementById('weather-soil-moisture').checked) tableHTML += '<th>Soil Moisture (%)</th>';
        if (document.getElementById('weather-wind-speed').checked) tableHTML += '<th>Wind Speed (km/h)</th>';
        if (document.getElementById('weather-pressure').checked) tableHTML += '<th>Pressure (hPa)</th>';
    } else {
        if (document.getElementById('irrigation-pump-status').checked) tableHTML += '<th>Pump Status</th>';
        if (document.getElementById('irrigation-water-level').checked) tableHTML += '<th>Water Level (%)</th>';
        if (document.getElementById('irrigation-duration').checked) tableHTML += '<th>Duration (s)</th>';
    }

    tableHTML += `
                    </tr>
                </thead>
                <tbody>
    `;

    // Add data rows
    data.forEach(item => {
        const timestamp = item.timestamp ? new Date(item.timestamp).toLocaleString() : 'N/A';
        tableHTML += `<tr><td>${timestamp}</td>`;

        if (reportType === 'weather') {
            if (document.getElementById('weather-temperature').checked) tableHTML += `<td>${item.temperature || 'N/A'}</td>`;
            if (document.getElementById('weather-humidity').checked) tableHTML += `<td>${item.humidity || 'N/A'}</td>`;
            if (document.getElementById('weather-soil-moisture').checked) tableHTML += `<td>${item.soil_moisture || 'N/A'}</td>`;
            if (document.getElementById('weather-wind-speed').checked) tableHTML += `<td>${item.wind_speed || 'N/A'}</td>`;
            if (document.getElementById('weather-pressure').checked) tableHTML += `<td>${item.pressure || 'N/A'}</td>`;
        } else {
            if (document.getElementById('irrigation-pump-status').checked) tableHTML += `<td>${item.pump_status ? 'Running' : 'Stopped'}</td>`;
            if (document.getElementById('irrigation-water-level').checked) tableHTML += `<td>${item.water_level || 'N/A'}</td>`;
            if (document.getElementById('irrigation-duration').checked) tableHTML += `<td>${item.duration || 'N/A'}</td>`;
        }

        tableHTML += `</tr>`;
    });

    tableHTML += `
                </tbody>
            </table>
        </div>
    `;

    reportDisplay.innerHTML = tableHTML;
}

function downloadReport() {
    const reportType = document.getElementById('report-type').value;
    
    // Get dates, defaulting to last 7 days if empty
    let startDate = document.getElementById('report-start-date').value;
    let endDate = document.getElementById('report-end-date').value;
    
    // If dates are empty, set them to default values and update the input fields
    if (!startDate || !endDate) {
        const today = new Date();
        const lastWeek = new Date(today);
        lastWeek.setDate(today.getDate() - 7);
        
        const formatDate = (date) => {
            return date.toISOString().split('T')[0];
        };
        
        if (!startDate) {
            startDate = formatDate(lastWeek);
            document.getElementById('report-start-date').value = startDate;
        }
        if (!endDate) {
            endDate = formatDate(today);
            document.getElementById('report-end-date').value = endDate;
        }
    }
    
    // Rest of the function remains the same
    // Get selected options
    const options = {};
    if (reportType === 'weather') {
        options.temperature = document.getElementById('weather-temperature').checked;
        options.humidity = document.getElementById('weather-humidity').checked;
        options.soil_moisture = document.getElementById('weather-soil-moisture').checked;
        options.wind_speed = document.getElementById('weather-wind-speed').checked;
        options.pressure = document.getElementById('weather-pressure').checked;
    } else {
        options.pump_status = document.getElementById('irrigation-pump-status').checked;
        options.water_level = document.getElementById('irrigation-water-level').checked;
        options.duration = document.getElementById('irrigation-duration').checked;
    }
    
    // Create URL with parameters
    const url = `/api/reports/download?report_type=${reportType}&start_date=${startDate}&end_date=${endDate}&options=${JSON.stringify(options)}`;
    
    // First check if data is available
    fetch(url)
        .then(response => {
            // Check if the response is JSON (our no-data message) or a file
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                // This is our JSON response, likely the no-data message
                return response.json().then(data => {
                    if (data.status === 'no_data') {
                        // Show popup with the message
                        alert(data.message);
                        return null;
                    }
                    return data;
                });
            } else {
                // This is a file download, trigger it
                response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    // Include dates in the filename
                    a.download = `${reportType}_report_${startDate}_to_${endDate}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                });
                return null;
            }
        })
        .catch(error => {
            console.error('Error downloading report:', error);
            alert('An error occurred while downloading the report. Please try again.');
        });}


// Variables to track irrigation
let irrigationStartTime = null;
let irrigationTimer = null;

// Function to start manual irrigation
function startManualIrrigation() {
    const presetId = getSelectedPresetId();
    
    if (!presetId) {
        showAlert('Please select a preset first', 'warning');
        return;
    }
    
    // Record the start time
    irrigationStartTime = Date.now();
    console.log("Starting irrigation at:", new Date(irrigationStartTime).toISOString());
    
    // Start a timer to update the elapsed time display
    const elapsedTimeDisplay = document.getElementById('elapsed-time');
    if (elapsedTimeDisplay) {
        irrigationTimer = setInterval(() => {
            const elapsedSeconds = Math.floor((Date.now() - irrigationStartTime) / 1000);
            elapsedTimeDisplay.textContent = formatTime(elapsedSeconds);
        }, 1000);
    }
    
    // Send the start command to the server
    fetch('/api/irrigation/manual', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'start',
            preset_id: presetId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update UI to show irrigation is running
            document.getElementById('start-irrigation').disabled = true;
            document.getElementById('stop-irrigation').disabled = false;
            showAlert('Irrigation started', 'success');
        } else {
            showAlert(data.message || 'Failed to start irrigation', 'danger');
        }
    })
    .catch(error => {
        console.error('Error starting irrigation:', error);
        showAlert('Error starting irrigation', 'danger');
    });
}

// Function to stop manual irrigation
function stopManualIrrigation() {
    // Calculate elapsed time
    let elapsedTime = 0;
    if (irrigationStartTime) {
        elapsedTime = (Date.now() - irrigationStartTime) / 1000; // Convert to seconds
        console.log("Stopping irrigation after:", elapsedTime, "seconds");
    }
    
    // Clear the timer
    if (irrigationTimer) {
        clearInterval(irrigationTimer);
        irrigationTimer = null;
    }
    
    // Reset start time
    irrigationStartTime = null;
    
    const presetId = getSelectedPresetId();
    
    // Send the stop command to the server with the elapsed time
    fetch('/api/irrigation/manual', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'stop',
            preset_id: presetId,
            elapsed_time: elapsedTime
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update UI to show irrigation is stopped
            document.getElementById('start-irrigation').disabled = false;
            document.getElementById('stop-irrigation').disabled = true;
            document.getElementById('elapsed-time').textContent = '00:00:00';
            showAlert('Irrigation stopped', 'success');
        } else {
            showAlert(data.message || 'Failed to stop irrigation', 'danger');
        }
    })
    .catch(error => {
        console.error('Error stopping irrigation:', error);
        showAlert('Error stopping irrigation', 'danger');
    });
}

// Helper function to format time as HH:MM:SS
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return [hours, minutes, secs]
        .map(v => v < 10 ? "0" + v : v)
        .join(":");
}
