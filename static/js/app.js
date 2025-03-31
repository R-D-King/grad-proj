// Initialize Socket.io connection
const socket = io();

// Variables for pump control
let pumpRunning = false;
let runningTime = 0;
let runningInterval;
let selectedPresetId = null;
let addPresetModal, addScheduleModal, editScheduleModal;

// Update current time
function updateTime() {
    const now = new Date();
    document.getElementById('current-time').innerText = now.toLocaleTimeString();
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap modals
    addPresetModal = new bootstrap.Modal(document.getElementById('addPresetModal'));
    addScheduleModal = new bootstrap.Modal(document.getElementById('addScheduleModal'));
    editScheduleModal = new bootstrap.Modal(document.getElementById('editScheduleModal'));

    // Load presets
    loadPresets();

    // Setup event listeners
    setupEventListeners();

    // Setup report type change handler
    document.getElementById('report-type').addEventListener('change', function () {
        const reportType = this.value;
        if (reportType === 'weather') {
            document.getElementById('weather-options').style.display = 'block';
            document.getElementById('irrigation-options').style.display = 'none';
        } else {
            document.getElementById('weather-options').style.display = 'none';
            document.getElementById('irrigation-options').style.display = 'block';
        }
    });
    
    // Add manual control button event listeners
    document.getElementById('manual-on-btn').addEventListener('click', startPump);
    document.getElementById('manual-off-btn').addEventListener('click', stopPump);
    
    // Set default dates for reports
    setDefaultDates();
    
    // Start updating time when page loads
    setInterval(updateTime, 1000);
    updateTime();
});

// Socket events for weather data
socket.on('weather_data', function (data) {
    document.getElementById('temp').innerText = data.temperature;
    document.getElementById('humidity').innerText = data.humidity;
    document.getElementById('soil-moisture').innerText = data.soil_moisture;
    document.getElementById('wind-speed').innerText = data.wind_speed;
    document.getElementById('pressure').innerText = data.pressure;
});

// Socket events for irrigation system
socket.on('pump_status', function (data) {
    const pumpStatus = document.getElementById('pump-status');
    pumpStatus.innerText = data.status ? 'Running' : 'Stopped';
    pumpStatus.className = data.status ? 'badge bg-success' : 'badge bg-secondary';

    if (data.status && !pumpRunning) {
        startRunningTimer();
    } else if (!data.status && pumpRunning) {
        stopRunningTimer();
    }
});

socket.on('water_level', function (data) {
    document.getElementById('water-level').innerText = data.level;
});

socket.on('running_preset', function(data) {
    const currentPresetElement = document.getElementById('current-preset');
    if (data && data.name) {
        currentPresetElement.textContent = data.name;
        
        // Highlight the active preset in the UI
        document.querySelectorAll('.preset-card').forEach(card => {
            if (card.dataset.presetId == data.id) {
                card.classList.add('running');
            } else {
                card.classList.remove('running');
            }
        });
    } else {
        currentPresetElement.textContent = 'None';
        document.querySelectorAll('.preset-card').forEach(card => {
            card.classList.remove('running');
        });
    }
});

// Socket events for preset management
socket.on('preset_updated', function (data) {
    loadPresets();
    if (selectedPresetId === data.id) {
        loadPresetDetails(selectedPresetId);
    }
});

socket.on('preset_deleted', function (data) {
    loadPresets();
    if (selectedPresetId === data.id) {
        selectedPresetId = null;
        document.getElementById('presetDetails').innerHTML = `
            <div class="text-center text-muted py-3">
                <p>Select a preset to view details</p>
            </div>
        `;
        document.getElementById('addScheduleBtn').disabled = true;
    }
});

socket.on('schedule_updated', function (data) {
    if (selectedPresetId === data.preset_id) {
        loadPresetDetails(selectedPresetId);
    }
});

socket.on('schedule_deleted', function (data) {
    if (selectedPresetId === data.preset_id) {
        loadPresetDetails(selectedPresetId);
    }
});

socket.on('preset_activated', function (data) {
    loadPresets();
});

// Functions for pump control
function startPump() {
    if (confirm('Are you sure you want to start the pump?')) {
        socket.emit('start_pump');
    }
}

function stopPump() {
    if (confirm('Are you sure you want to stop the pump?')) {
        socket.emit('stop_pump');
    }
}

function startRunningTimer() {
    pumpRunning = true;
    runningTime = 0;
    document.getElementById('running-time').innerText = runningTime;
    runningInterval = setInterval(function () {
        runningTime++;
        document.getElementById('running-time').innerText = runningTime;
    }, 1000);
}

function stopRunningTimer() {
    pumpRunning = false;
    clearInterval(runningInterval);
    runningTime = 0;
    document.getElementById('running-time').innerText = runningTime;
}

// Function to set default dates for reports
function setDefaultDates() {
    const today = new Date();
    const lastWeek = new Date();
    lastWeek.setDate(today.getDate() - 7);
    
    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    document.getElementById('report-start-date').value = formatDate(lastWeek);
    document.getElementById('report-end-date').value = formatDate(today);
}

// Setup event listeners for preset management
function setupEventListeners() {
    // Preset management
    document.getElementById('addPresetBtn').addEventListener('click', () => addPresetModal.show());
    document.getElementById('savePresetBtn').addEventListener('click', saveNewPreset);

    // Schedule management
    document.getElementById('addScheduleBtn').addEventListener('click', () => addScheduleModal.show());
    document.getElementById('saveScheduleBtn').addEventListener('click', saveNewSchedule);
    document.getElementById('updateScheduleBtn').addEventListener('click', updateSchedule);
}

// Load all presets
function loadPresets() {
    fetch('/api/irrigation/presets')
        .then(response => response.json())
        .then(data => {
            const presetsList = document.getElementById('presetsList');
            presetsList.innerHTML = '';
            data.forEach(preset => {
                const presetCard = document.createElement('div');
                presetCard.className = 'col-6 mb-2';
                presetCard.innerHTML = `
                    <div class="card preset-card ${preset.active ? 'active' : ''}" data-preset-id="${preset.id}">
                        <div class="card-body p-2 text-center">
                            <h6 class="mb-0">${preset.name}</h6>
                            <small class="text-muted">${preset.schedules.length} schedules</small>
                        </div>
                    </div>
                `;
                presetCard.querySelector('.preset-card').addEventListener('click', () => selectPreset(preset.id));
                presetsList.appendChild(presetCard);
            });
        })
        .catch(error => console.error('Error loading presets:', error));
}

// Select a preset
function selectPreset(presetId) {
    selectedPresetId = presetId;

    // Update UI to show selected preset
    document.querySelectorAll('.preset-card').forEach(card => {
        card.classList.remove('active');
        if (parseInt(card.dataset.presetId) === presetId) {
            card.classList.add('active');
        }
    });

    // Enable add schedule button
    document.getElementById('addScheduleBtn').disabled = false;

    // Load preset details
    loadPresetDetails(presetId);

    // Activate the preset
    fetch(`/api/irrigation/preset/${presetId}/activate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .catch(error => console.error('Error activating preset:', error));
}

// Load preset details
function loadPresetDetails(presetId) {
    fetch(`/api/irrigation/preset/${presetId}`)
        .then(response => response.json())
        .then(data => {
            const presetDetails = document.getElementById('presetDetails');
            presetDetails.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5>${data.name}</h5>
                    <div>
                        <button class="btn btn-sm btn-danger delete-preset-btn" data-preset-id="${data.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <h6 class="mb-3">Schedules:</h6>
                <div id="schedulesList">
                    ${data.schedules.length === 0 ?
                    '<p class="text-muted">No schedules added yet</p>' :
                    data.schedules.map(schedule => `
                            <div class="schedule-item d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="d-flex align-items-center">
                                        <span class="badge ${schedule.active ? 'bg-success' : 'bg-secondary'} me-2">
                                            ${schedule.active ? 'Active' : 'Inactive'}
                                        </span>
                                        <strong>${schedule.start_time}</strong>
                                    </div>
                                    <small class="text-muted">Duration: ${schedule.duration}s</small>
                                </div>
                                <div>
                                    <button class="btn btn-sm btn-primary edit-schedule-btn" 
                                        data-schedule-id="${schedule.id}"
                                        data-start-time="${schedule.start_time}"
                                        data-duration="${schedule.duration}"
                                        data-active="${schedule.active}">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger delete-schedule-btn" data-schedule-id="${schedule.id}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        `).join('')
                }
                </div>
            `;

            // Add event listeners for schedule management
            document.querySelectorAll('.edit-schedule-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const scheduleId = e.currentTarget.dataset.scheduleId;
                    const startTime = e.currentTarget.dataset.startTime;
                    const duration = e.currentTarget.dataset.duration;
                    const active = e.currentTarget.dataset.active === 'true';

                    document.getElementById('editScheduleId').value = scheduleId;
                    document.getElementById('editScheduleTime').value = startTime;
                    document.getElementById('editScheduleDuration').value = duration;
                    document.getElementById('editScheduleActive').checked = active;

                    editScheduleModal.show();
                });
            });

            document.querySelectorAll('.delete-schedule-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const scheduleId = e.currentTarget.dataset.scheduleId;
                    if (confirm('Are you sure you want to delete this schedule?')) {
                        deleteSchedule(scheduleId);
                    }
                });
            });

            document.querySelectorAll('.delete-preset-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const presetId = e.currentTarget.dataset.presetId;
                    if (confirm('Are you sure you want to delete this preset?')) {
                        deletePreset(presetId);
                    }
                });
            });

            document.querySelectorAll('.rename-preset-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const presetId = e.currentTarget.dataset.presetId;
                    const currentName = e.currentTarget.dataset.presetName;
                    const newName = prompt('Enter new preset name:', currentName);

                    if (newName && newName !== currentName) {
                        renamePreset(presetId, newName);
                    }
                });
            });
        })
        .catch(error => console.error('Error loading preset details:', error));
}

// Save new preset
function saveNewPreset() {
    const presetName = document.getElementById('presetName').value;

    if (!presetName) {
        alert('Please enter a preset name');
        return;
    }

    fetch('/api/irrigation/preset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: presetName,
            schedules: []
        })
    })
        .then(response => response.json())
        .then(data => {
            addPresetModal.hide();
            document.getElementById('presetName').value = '';
            loadPresets();
        })
        .catch(error => console.error('Error saving preset:', error));
}

// Delete preset
function deletePreset(presetId) {
    fetch(`/api/irrigation/preset/${presetId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            console.log('Preset deleted:', data);
        })
        .catch(error => console.error('Error deleting preset:', error));
}

// Save new schedule
function saveNewSchedule() {
    const startTime = document.getElementById('scheduleTime').value;
    const duration = document.getElementById('scheduleDuration').value;

    if (!startTime || !duration) {
        alert('Please fill all fields');
        return;
    }

    fetch('/api/irrigation/schedule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start_time: startTime,
            duration: duration,
            preset_id: selectedPresetId
        })
    })
        .then(response => response.json())
        .then(data => {
            addScheduleModal.hide();
            document.getElementById('scheduleTime').value = '';
            document.getElementById('scheduleDuration').value = '';
            loadPresetDetails(selectedPresetId);
        })
        .catch(error => console.error('Error saving schedule:', error));
}

// Update schedule
function updateSchedule() {
    const scheduleId = document.getElementById('editScheduleId').value;
    const startTime = document.getElementById('editScheduleTime').value;
    const duration = document.getElementById('editScheduleDuration').value;
    const active = document.getElementById('editScheduleActive').checked;

    fetch(`/api/irrigation/schedule/${scheduleId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start_time: startTime,
            duration: duration,
            active: active
        })
    })
        .then(response => response.json())
        .then(data => {
            editScheduleModal.hide();
        })
        .catch(error => console.error('Error updating schedule:', error));
}

// Delete schedule
function deleteSchedule(scheduleId) {
    fetch(`/api/irrigation/schedule/${scheduleId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            console.log('Schedule deleted:', data);
        })
        .catch(error => console.error('Error deleting schedule:', error));
}

// Report generation functions
function generateReport() {
    const reportType = document.getElementById('report-type').value;
    const startDate = document.getElementById('report-start-date').value;
    const endDate = document.getElementById('report-end-date').value;

    if (!startDate || !endDate) {
        alert('Please select start and end dates');
        return;
    }

    let options = {};

    if (reportType === 'weather') {
        options = {
            temperature: document.getElementById('weather-temperature').checked,
            humidity: document.getElementById('weather-humidity').checked,
            soil_moisture: document.getElementById('weather-soil-moisture').checked,
            wind_speed: document.getElementById('weather-wind-speed').checked,
            pressure: document.getElementById('weather-pressure').checked
        };
    } else {
        options = {
            pump_status: document.getElementById('irrigation-pump-status').checked,
            water_level: document.getElementById('irrigation-water-level').checked,
            duration: document.getElementById('irrigation-duration').checked
        };
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

    if (data.length === 0) {
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
        tableHTML += `<tr><td>${new Date(item.timestamp).toLocaleString()}</td>`;

        if (reportType === 'weather') {
            if (document.getElementById('weather-temperature').checked) tableHTML += `<td>${item.temperature}</td>`;
            if (document.getElementById('weather-humidity').checked) tableHTML += `<td>${item.humidity}</td>`;
            if (document.getElementById('weather-soil-moisture').checked) tableHTML += `<td>${item.soil_moisture}</td>`;
            if (document.getElementById('weather-wind-speed').checked) tableHTML += `<td>${item.wind_speed}</td>`;
            if (document.getElementById('weather-pressure').checked) tableHTML += `<td>${item.pressure}</td>`;
        } else {
            if (document.getElementById('irrigation-pump-status').checked) tableHTML += `<td>${item.pump_status ? 'Running' : 'Stopped'}</td>`;
            if (document.getElementById('irrigation-water-level').checked) tableHTML += `<td>${item.water_level}</td>`;
            if (document.getElementById('irrigation-duration').checked) tableHTML += `<td>${item.duration}</td>`;
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

function clearReports() {
    document.getElementById('report-display').innerHTML = '';
}

// Function to download report
function downloadReport() {
    const reportType = document.getElementById('report-type').value;
    const startDate = document.getElementById('report-start-date').value;
    const endDate = document.getElementById('report-end-date').value;
    
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
        });
}