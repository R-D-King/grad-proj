// Main Application JavaScript

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application initialized');
    
    // Initialize modules
    initializeModules();
    
    // Set up event listeners
    setupEventListeners();
    
    // Set up clock with reduced frequency (every 10 seconds)
    updateServerTime();
    setInterval(updateServerTime, 10000);
    
    // Use local clock for second-by-second updates
    setInterval(updateLocalTime, 1000);
});

// Function to update server time
function updateServerTime() {
    const timeDisplay = document.getElementById('server-time-display');
    if (timeDisplay) {
        fetch('/api/server-time/display')
            .then(response => response.json())
            .then(data => {
                timeDisplay.textContent = data.formatted_time || '00:00:00';
                timeDisplay.classList.remove('text-danger');
                // Store last successful time update
                window.lastTimeUpdate = Date.now();
            })
            .catch(error => {
                console.error('Error fetching server time:', error);
                // If it's been more than 5 seconds since last update, show offline
                if (!window.lastTimeUpdate || Date.now() - window.lastTimeUpdate > 5000) {
                    timeDisplay.textContent = 'OFFLINE';
                    timeDisplay.classList.add('text-danger');
                }
            });
    }
}

// Function to update time locally between server syncs
function updateLocalTime() {
    const timeDisplay = document.getElementById('server-time-display');
    // Only update locally if we're not in offline mode
    if (timeDisplay && !timeDisplay.classList.contains('text-danger')) {
        const now = new Date();
        // Format consistently in 24-hour format
        timeDisplay.textContent = now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

// Function to initialize all modules
function initializeModules() {
    console.log('Initializing modules');
    
    // Initialize report options if the element exists
    const reportTypeSelect = document.getElementById('report-type');
    if (reportTypeSelect) {
        toggleReportOptions();
    }
    
    // Load weather data
    loadWeatherData();
    
    // Load irrigation status
    loadIrrigationStatus();
}

// Function to load weather data
function loadWeatherData() {
    fetch('/api/weather/current')
        .then(response => response.json())
        .then(data => {
            if (data) {
                // Use a more efficient approach to update multiple elements
                updateElementText('temp', data.temperature);
                updateElementText('humidity', data.humidity);
                updateElementText('soil-moisture', data.soil_moisture);
                updateElementText('wind-speed', data.wind_speed);
                updateElementText('pressure', data.pressure);
            }
        })
        .catch(error => {
            console.error('Error loading weather data:', error);
        });
}

// Helper function to update element text with fallback
function updateElementText(elementId, value, fallback = '--') {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value || fallback;
    }
}

// Helper function to update element class
function updateElementClass(elementId, newClass, fallbackClass = '') {
    const element = document.getElementById(elementId);
    if (element) {
        // Remove all existing classes that might conflict
        element.className = '';
        // Add the new class if it exists, otherwise add fallback
        element.className = newClass || fallbackClass;
    }
}

// Helper function to get water level class based on percentage
function getWaterLevelClass(level) {
    if (level === undefined || level === null) return 'text-warning';
    const numLevel = Number(level);
    if (isNaN(numLevel)) return 'text-warning';
    
    if (numLevel <= 20) return 'text-danger';
    if (numLevel <= 40) return 'text-warning';
    return 'text-success';
}

// Global variables for pump timer
let pumpTimerInterval = null;

// Function to load irrigation status
function loadIrrigationStatus() {
    fetch('/api/irrigation/status')
        .then(response => response.json())
        .then(data => {
            // Update pump status
            const pumpStatus = data.pump_status;
            
            // Update the pumpRunning variable
            if (typeof pumpStatus === 'object' && pumpStatus !== null) {
                pumpRunning = pumpStatus.running || false;
                
                if (!pumpRunning) {
                    lastPumpStopTime = Date.now();
                }
                
                // Update UI elements
                const pumpStatusElement = document.getElementById('pump-status');
                if (pumpStatusElement) {
                    pumpStatusElement.textContent = pumpStatus.running ? 'Running' : 'Stopped';
                    pumpStatusElement.className = pumpStatus.running ? 'badge bg-success' : 'badge bg-danger';
                }
            } else {
                // Legacy support for boolean pump status
                pumpRunning = !!pumpStatus;
                
                if (!pumpRunning) {
                    lastPumpStopTime = Date.now();
                }
                
                // Update UI elements
                const pumpStatusElement = document.getElementById('pump-status');
                if (pumpStatusElement) {
                    pumpStatusElement.textContent = pumpStatus ? 'Running' : 'Stopped';
                    pumpStatusElement.className = pumpStatus ? 'badge bg-success' : 'badge bg-danger';
                }
            }
            
            // Update water level
            const waterLevel = data.water_level;
            if (waterLevel) {
                // Fix: Check if waterLevel is an object with a level property
                if (typeof waterLevel === 'object' && waterLevel.level !== undefined) {
                    // Remove any existing % sign before adding one
                    const levelValue = Math.round(waterLevel.level);
                    updateElementText('water-level', `${levelValue}%`, 'Unknown');
                } else {
                    // Handle case where waterLevel is a direct number value
                    const levelValue = Math.round(waterLevel);
                    updateElementText('water-level', `${levelValue}%`, 'Unknown');
                }
            }
            
            // Start or stop the pump duration timer based on pump status
            if (pumpRunning) {
                updatePumpDurationFromServer();
                // Start interval to update duration every second if not already running
                if (!pumpTimerInterval) {
                    pumpTimerInterval = setInterval(updatePumpDurationFromServer, 1000);
                }
            } else {
                // Stop the timer if pump is not running, but wait a moment to get final duration
                if (pumpTimerInterval) {
                    // Get one final update to ensure we have the latest duration
                    updatePumpDurationFromServer();
                    
                    // Then stop the timer after a short delay
                    setTimeout(() => {
                        clearInterval(pumpTimerInterval);
                        pumpTimerInterval = null;
                    }, 2000);
                }
            }
        })
        .catch(error => {
            console.error('Error loading irrigation status:', error);
            // Try again after a delay
            setTimeout(loadIrrigationStatus, 5000);
        });
}

// Function to update pump duration from server
function updatePumpDurationFromServer() {
    fetch('/api/irrigation/pump/duration')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Update the running-time element with the duration in seconds
            const runningTimeElement = document.getElementById('running-time');
            if (runningTimeElement) {
                // Convert to integer by using Math.floor
                const seconds = Math.floor(data.seconds || 0);
                runningTimeElement.textContent = seconds;
            }
        })
        .catch(error => {
            console.error('Error updating pump duration:', error);
        });
}

// Function to handle pump actions
function handlePumpAction(action, startBtn, stopBtn) {
    // Disable buttons during operation
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = true;
    
    fetch(`/api/irrigation/pump/${action}`, { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log(`Pump ${action} response:`, data);
        
        // Update pump status based on action
        if (action === 'start' && data.status === 'success') {
            pumpRunning = true;
        } else if (action === 'stop' && data.status === 'success') {
            pumpRunning = false;
            lastPumpStopTime = Date.now();
        }
        
        // Show alert with proper styling
        showAlert(data.message, data.status === 'success' ? 'success' : 
                             data.status === 'warning' ? 'warning' : 'danger');
        
        // Refresh irrigation status
        loadIrrigationStatus();
    })
    .catch(error => {
        console.error(`Error ${action}ing pump:`, error);
        showAlert(`Error ${action}ing pump. Please try again.`, 'danger');
    })
    .finally(() => {
        // Re-enable buttons
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = false;
    });
}

// Function to set up event listeners
function setupEventListeners() {
    console.log('Setting up event listeners');
    
    // Set up report type change listener
    const reportTypeSelect = document.getElementById('report-type');
    if (reportTypeSelect) {
        reportTypeSelect.addEventListener('change', toggleReportOptions);
    }
    
    // Set up pump control buttons
    setupPumpControls();
    
    // Set up preset buttons
    setupPresetButtons();
}

// Function to set up pump controls
function setupPumpControls() {
    const startPumpBtn = document.getElementById('manual-on-btn');
    const stopPumpBtn = document.getElementById('manual-off-btn');
    
    if (startPumpBtn) {
        startPumpBtn.addEventListener('click', function() {
            handlePumpAction('start', startPumpBtn, stopPumpBtn);
        });
    }
    
    if (stopPumpBtn) {
        stopPumpBtn.addEventListener('click', function() {
            handlePumpAction('stop', startPumpBtn, stopPumpBtn);
        });
    }
}

// Function to handle pump actions
function handlePumpAction(action, startBtn, stopBtn) {
    // Disable buttons during operation
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = true;
    
    fetch(`/api/irrigation/pump/${action}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`Pump ${action} response:`, data);
            showAlert(data.message, data.status);
            loadIrrigationStatus();
        })
        .catch(error => {
            console.error(`Error ${action}ing pump:`, error);
            showAlert(`Error ${action}ing pump. Please try again.`, 'danger');
            
            // Force refresh irrigation status to get accurate state
            setTimeout(loadIrrigationStatus, 1000);
        })
        .finally(() => {
            // Re-enable buttons
            if (startBtn) startBtn.disabled = false;
            if (stopBtn) stopBtn.disabled = false;
        });
}

// Function to set up preset buttons
function setupPresetButtons() {
    // Load presets
    loadPresets();
    
    // Add preset button
    const addPresetBtn = document.getElementById('add-preset-btn');
    if (addPresetBtn) {
        addPresetBtn.addEventListener('click', function() {
            const presetName = document.getElementById('new-preset-name').value;
            if (!presetName) {
                showAlert('Please enter a preset name', 'warning');
                return;
            }
            
            fetch('/api/irrigation/presets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: presetName })
            })
            .then(response => response.json())
            .then(data => {
                showAlert(data.message || `Preset "${presetName}" created`, 'success');
                loadPresets();
                document.getElementById('new-preset-name').value = '';
            })
            .catch(error => {
                console.error('Error creating preset:', error);
                showAlert('Error creating preset', 'danger');
            });
        });
    }
}

// Function to load presets
function loadPresets() {
    const presetsList = document.getElementById('presets-list');
    if (!presetsList) return;
    
    fetch('/api/irrigation/presets')  // This should match the backend route
        .then(response => response.json())
        .then(presets => {
            presetsList.innerHTML = '';
            
            if (presets.length === 0) {
                presetsList.innerHTML = '<div class="list-group-item">No presets available</div>';
                return;
            }
            
            presets.forEach(preset => {
                const presetItem = document.createElement('div');
                presetItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                
                const activeClass = preset.active ? 'bg-success text-white' : '';
                presetItem.classList.add(...activeClass.split(' ').filter(c => c));
                
                presetItem.innerHTML = `
                    <span>${preset.name}</span>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-primary activate-preset" data-id="${preset.id}">
                            Activate
                        </button>
                        <button type="button" class="btn btn-sm btn-danger delete-preset" data-id="${preset.id}">
                            Delete
                        </button>
                    </div>
                `;
                
                presetsList.appendChild(presetItem);
            });
            
            // Add event listeners to the new buttons
            document.querySelectorAll('.activate-preset').forEach(button => {
                button.addEventListener('click', function() {
                    const presetId = this.getAttribute('data-id');
                    activatePreset(presetId);
                });
            });
            
            document.querySelectorAll('.delete-preset').forEach(button => {
                button.addEventListener('click', function() {
                    const presetId = this.getAttribute('data-id');
                    deletePreset(presetId);
                });
            });
        })
        .catch(error => {
            console.error('Error loading presets:', error);
            presetsList.innerHTML = '<div class="list-group-item text-danger">Error loading presets</div>';
        });
}

// Function to activate a preset
function activatePreset(presetId) {
    fetch(`/api/irrigation/preset/${presetId}/activate`, {  // Update to match backend route
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        showAlert(`Preset "${data.name}" activated`, 'success');
        loadPresets();
        // Refresh irrigation status as preset may have changed pump state
        loadIrrigationStatus();
    })
    .catch(error => {
        console.error('Error activating preset:', error);
        showAlert('Error activating preset', 'danger');
    });
}

// Function to delete a preset
function deletePreset(presetId) {
    if (!confirm('Are you sure you want to delete this preset?')) {
        return;
    }
    
    fetch(`/api/irrigation/preset/${presetId}`, {  // Update to match backend route
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        showAlert(data.message, 'success');
        loadPresets();
    })
    .catch(error => {
        console.error('Error deleting preset:', error);
        showAlert('Error deleting preset', 'danger');
    });
}

// Function to show alerts
function showAlert(message, type = 'info') {
    // Create alerts container if it doesn't exist
    let alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) {
        alertsContainer = document.createElement('div');
        alertsContainer.id = 'alerts-container';
        alertsContainer.style.position = 'fixed';
        alertsContainer.style.top = '20px';
        alertsContainer.style.right = '20px';
        alertsContainer.style.zIndex = '1050';
        document.body.appendChild(alertsContainer);
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertsContainer.removeChild(alertDiv);
        }, 150);
    }, 5000);
}

// Function to toggle report options based on report type
function toggleReportOptions() {
    const reportType = document.getElementById('report-type').value;
    console.log(`Report type changed to: ${reportType}`);
    
    // Get option containers
    const weatherOptions = document.getElementById('weather-options');
    const irrigationOptions = document.getElementById('irrigation-options');
    
    if (!weatherOptions || !irrigationOptions) {
        console.error('Report option containers not found');
        return;
    }
    
    // Show/hide based on report type
    if (reportType === 'weather') {
        weatherOptions.style.display = 'block';
        irrigationOptions.style.display = 'none';
    } else {
        weatherOptions.style.display = 'none';
        irrigationOptions.style.display = 'block';
    }
    
    console.log(`Toggled options for ${reportType} report`);
}

// Function to set default dates if they're empty
function setDefaultDates() {
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
    
    return { startDate, endDate };
}

// Function to generate a report
function generateReport() {
    const reportType = document.getElementById('report-type').value;
    
    // Set default dates if empty
    const { startDate, endDate } = setDefaultDates();
    
    // Get selected options
    const options = getReportOptions(reportType);
    
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
        console.log('Report data:', data);
        displayReport(data, reportType);
    })
    .catch(error => {
        console.error('Error generating report:', error);
        showAlert('Error generating report. Please try again.', 'danger');
    });
}

// Helper function to get report options
function getReportOptions(reportType) {
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
    
    return options;
}

// Function to display a report
function displayReport(data, reportType) {
    const reportDisplay = document.getElementById('report-display');
    if (!reportDisplay) {
        console.error('Report display container not found');
        return;
    }
    
    if (!data || data.length === 0) {
        reportDisplay.innerHTML = '<div class="alert alert-info">No data available for the selected period.</div>';
        return;
    }
    
    // Create table headers based on report type and available data
    let headers = ['Date', 'Time'];
    
    // Get the selected options
    const options = getReportOptions(reportType);
    
    if (reportType === 'weather') {
        // Add weather-specific headers based on selected options
        if (options.temperature) headers.push('Temperature (°C)');
        if (options.humidity) headers.push('Humidity (%)');
        if (options.soil_moisture) headers.push('Soil Moisture (%)');
        if (options.wind_speed) headers.push('Wind Speed (km/h)');
        if (options.pressure) headers.push('Pressure (hPa)');
    } else {
        // Add irrigation-specific headers based on selected options
        if (options.pump_status) headers.push('Pump Status');
        if (options.water_level) headers.push('Water Level (%)');
        if (options.duration) headers.push('Duration (s)');
    }
    
    // Create table HTML
    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        ${headers.map(header => `<th>${header}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add rows for each data point
    data.forEach(item => {
        const timestamp = new Date(item.timestamp);
        const date = timestamp.toLocaleDateString();
        const time = timestamp.toLocaleTimeString();
        
        tableHTML += '<tr>';
        tableHTML += `<td>${date}</td>`;
        tableHTML += `<td>${time}</td>`;
        
        if (reportType === 'weather') {
            // Add weather-specific data based on selected options
            if (options.temperature) tableHTML += `<td>${item.temperature !== undefined ? item.temperature : '-'}</td>`;
            if (options.humidity) tableHTML += `<td>${item.humidity !== undefined ? item.humidity : '-'}</td>`;
            if (options.soil_moisture) tableHTML += `<td>${item.soil_moisture !== undefined ? item.soil_moisture : '-'}</td>`;
            if (options.wind_speed) tableHTML += `<td>${item.wind_speed !== undefined ? item.wind_speed : '-'}</td>`;
            if (options.pressure) tableHTML += `<td>${item.pressure !== undefined ? item.pressure : '-'}</td>`;
        } else {
            // Add irrigation-specific data based on selected options
            if (options.pump_status) tableHTML += `<td>${item.pump_status !== undefined ? (item.pump_status ? 'Running' : 'Stopped') : '-'}</td>`;
            if (options.water_level) tableHTML += `<td>${item.water_level !== undefined ? item.water_level : '-'}</td>`;
            if (options.duration) tableHTML += `<td>${item.duration !== undefined ? item.duration : '-'}</td>`;
        }
        
        tableHTML += '</tr>';
    });
    
    tableHTML += `
                </tbody>
            </table>
        </div>
    `;
    
    reportDisplay.innerHTML = tableHTML;
}

// Function to download a report
function downloadReport() {
    const reportType = document.getElementById('report-type').value;
    
    // Set default dates if empty
    const { startDate, endDate } = setDefaultDates();
    
    // Get selected options
    const options = getReportOptions(reportType);
    
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
                        showAlert(data.message, 'warning');
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
                    
                    showAlert('Report downloaded successfully', 'success');
                });
                return null;
            }
        })
        .catch(error => {
            console.error('Error downloading report:', error);
            showAlert('Error downloading report. Please try again.', 'danger');
        });
}

// Function to clear the report display
function clearReports() {
    const reportDisplay = document.getElementById('report-display');
    if (reportDisplay) {
        reportDisplay.innerHTML = '';
        console.log('Reports cleared');
        showAlert('Report display cleared', 'info');
    }
}

// Make functions available globally
window.generateReport = generateReport;
window.downloadReport = downloadReport;
window.clearReports = clearReports;
window.toggleReportOptions = toggleReportOptions;