// --- GLOBALS ---
let presets = [];
let activePreset = null;
let selectedPresetId = null;
let serverTimeOffset = 0;

// --- DOMContentLoaded ---
document.addEventListener('DOMContentLoaded', () => {
    initializeSocketIO();
    initializeEventListeners();
    initializeClock();
    loadAndDisplayPresets();
    updatePumpStatus(); // Initial check
});

// --- INITIALIZATION ---
function initializeSocketIO() {
    const socket = io();

    socket.on('connect', () => {
        console.log('Connected to server via Socket.IO');
    });

    socket.on('sensor_update', (data) => {
        updateSensorReadings(data);
    });

    socket.on('sensor_status_update', (statuses) => {
        updateSensorStatuses(statuses);
    });

    socket.on('pump_status_update', (data) => {
        updatePumpStatusUI(data);
    });
}

function initializeEventListeners() {
    // Preset buttons
    document.getElementById('addPresetBtn').addEventListener('click', () => openPresetModal());
    document.getElementById('savePresetBtn').addEventListener('click', savePreset);
    
    // Preset detail buttons are handled dynamically in displayPresetDetails
    
    // Schedule buttons
    document.getElementById('addScheduleBtn').addEventListener('click', () => openScheduleModal());
    document.getElementById('saveScheduleBtn').addEventListener('click', saveSchedule);

    // Manual pump controls
    document.getElementById('manual-on-btn').addEventListener('click', () => manualPumpControl('start'));
    document.getElementById('manual-off-btn').addEventListener('click', () => manualPumpControl('stop'));
}

async function initializeClock() {
    try {
        const response = await fetch('/api/server-time');
        const data = await response.json();
        const serverTime = new Date(data.time);
        const clientTime = new Date();
        serverTimeOffset = serverTime - clientTime;

        setInterval(updateClock, 1000);
        updateClock(); // Initial display
    } catch (error) {
        console.error('Failed to initialize clock:', error);
        document.getElementById('server-time-display').textContent = 'Error';
    }
}

function updateClock() {
    const now = new Date(new Date().getTime() + serverTimeOffset);
    const timeString = now.toLocaleTimeString();
    document.getElementById('server-time-display').textContent = timeString;
}


// --- PRESET MANAGEMENT ---

async function loadAndDisplayPresets() {
    try {
        const response = await fetch('/api/presets');
        presets = await response.json();
        
        const presetsList = document.getElementById('presetsList');
        presetsList.innerHTML = '';

        activePreset = null; // Reset active preset

        if (presets.length === 0) {
            presetsList.innerHTML = '<div class="text-muted text-center p-3">No presets configured.</div>';
        } else {
            presets.forEach(p => {
                const a = document.createElement('a');
                a.href = '#';
                // The 'active' class from bootstrap is for the active *item*, not our custom preset state
                a.className = `list-group-item list-group-item-action`;
                if (p.is_active) {
                    a.classList.add('active'); // Bootstrap's active class for styling
                    activePreset = p;
                }
                a.dataset.id = p.id;
                a.textContent = p.name;
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    selectPreset(p.id);
                });
                presetsList.appendChild(a);
            });
        }
        updateActivePresetUI();
    } catch (error) {
        console.error('Failed to load presets:', error);
        showAlert('Failed to load presets.', 'danger');
    }
}

function selectPreset(presetId) {
    if (selectedPresetId === presetId) {
        // Deselect if clicking the same preset again
        selectedPresetId = null;
        document.getElementById('presetDetails').classList.add('d-none');
        document.getElementById('noPresetSelected').classList.remove('d-none');
        document.querySelectorAll('#presetsList a').forEach(a => a.classList.remove('bg-light'));
    } else {
        selectedPresetId = presetId;
        // Update visual selection indicator
        document.querySelectorAll('#presetsList a').forEach(a => {
            a.classList.toggle('bg-light', a.dataset.id == presetId);
        });
        displayPresetDetails(presetId);
    }
}

function displayPresetDetails(presetId) {
    const preset = presets.find(p => p.id === presetId);
    if (!preset) return;

    // --- Update Headers and Buttons ---
    document.getElementById('presetNameHeader').textContent = preset.name;
    document.getElementById('presetDescription').textContent = preset.description || 'No description provided.';
    
    // Get buttons
    const activateBtn = document.getElementById('activatePresetBtn');
    const editBtn = document.getElementById('editPresetBtn');
    const deleteBtn = document.getElementById('deletePresetBtn');

    // Clone buttons to remove old event listeners
    const newActivateBtn = activateBtn.cloneNode(true);
    const newEditBtn = editBtn.cloneNode(true);
    const newDeleteBtn = deleteBtn.cloneNode(true);
    
    // Configure Activate/Deactivate Button
    const presetIsActive = preset.is_active;
    newActivateBtn.innerHTML = presetIsActive ? '<i class="fas fa-times"></i> Deactivate' : '<i class="fas fa-check"></i> Activate';
    newActivateBtn.classList.toggle('btn-success', !presetIsActive);
    newActivateBtn.classList.toggle('btn-warning', presetIsActive);
    if (presetIsActive) {
        newActivateBtn.addEventListener('click', deactivatePreset);
    } else {
        newActivateBtn.addEventListener('click', activatePreset);
    }

    // Add listeners to other buttons
    newEditBtn.addEventListener('click', () => openPresetModal(preset.id));
    newDeleteBtn.addEventListener('click', deletePreset);

    // Replace old buttons with new ones
    activateBtn.parentNode.replaceChild(newActivateBtn, activateBtn);
    editBtn.parentNode.replaceChild(newEditBtn, editBtn);
    deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);

    // --- Update Schedule Table ---
    const scheduleList = document.getElementById('scheduleList');
    scheduleList.innerHTML = '';
    if (preset.schedules && preset.schedules.length > 0) {
        preset.schedules.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.day_of_week}</td>
                <td>${s.start_time}</td>
                <td>${s.duration_seconds}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteSchedule(${s.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            scheduleList.appendChild(tr);
        });
    } else {
        scheduleList.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No schedules for this preset.</td></tr>';
    }

    // Show the details view
    document.getElementById('presetDetails').classList.remove('d-none');
    document.getElementById('noPresetSelected').classList.add('d-none');
}

async function savePreset() {
    const presetId = document.getElementById('presetId').value;
    const isEdit = !!presetId;
    const name = document.getElementById('presetName').value;
    const description = document.getElementById('presetDescriptionInput').value;

    if (!name) {
        showAlert('Preset name is required.', 'warning');
        return;
    }

    const url = isEdit ? `/api/presets/${presetId}` : '/api/presets';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, description })
        });

        if (!response.ok) throw new Error('Failed to save preset');
        
        const updatedPreset = await response.json();
        
        showAlert(`Preset ${isEdit ? 'updated' : 'created'} successfully!`, 'success');
        bootstrap.Modal.getInstance(document.getElementById('addPresetModal')).hide();
        
        await loadAndDisplayPresets();
        selectPreset(updatedPreset.id); // Select the new/edited preset
        
    } catch (error) {
        console.error('Error saving preset:', error);
        showAlert('Failed to save preset.', 'danger');
    }
}

async function deletePreset() {
    if (!selectedPresetId || !confirm('Are you sure you want to delete this preset?')) return;
    
    try {
        await fetch(`/api/presets/${selectedPresetId}`, { method: 'DELETE' });
        showAlert('Preset deleted successfully!', 'success');
        selectedPresetId = null;
        document.getElementById('presetDetails').classList.add('d-none');
        document.getElementById('noPresetSelected').classList.remove('d-none');
        loadAndDisplayPresets();
    } catch (error) {
        console.error('Error deleting preset:', error);
        showAlert('Failed to delete preset.', 'danger');
    }
}

async function activatePreset() {
    if (!selectedPresetId) return;
    try {
        const response = await fetch(`/api/presets/${selectedPresetId}/activate`, { method: 'POST' });
        activePreset = await response.json();
        showAlert(`Preset "${activePreset.name}" is now active.`, 'success');
        await loadAndDisplayPresets();
        selectPreset(activePreset.id);
    } catch (error) {
        console.error('Error activating preset:', error);
        showAlert('Failed to activate preset.', 'danger');
    }
}

async function deactivatePreset() {
    if (!confirm('Are you sure you want to deactivate the current preset?')) return;
    try {
        await fetch(`/api/presets/deactivate`, { method: 'POST' });
        activePreset = null;
        showAlert('The active preset has been deactivated.', 'success');
        await loadAndDisplayPresets();
        // Hide details view
        document.getElementById('presetDetails').classList.add('d-none');
        document.getElementById('noPresetSelected').classList.remove('d-none');
    } catch (error) {
        console.error('Error deactivating preset:', error);
        showAlert('Failed to deactivate preset.', 'danger');
    }
}

// --- SCHEDULE MANAGEMENT ---

async function saveSchedule() {
    if (!selectedPresetId) return;

    const scheduleData = {
        day_of_week: document.getElementById('scheduleDayOfWeek').value,
        start_time: document.getElementById('scheduleStartTime').value,
        duration_seconds: parseInt(document.getElementById('scheduleDuration').value, 10)
    };

    if (!scheduleData.day_of_week || !scheduleData.start_time || !scheduleData.duration_seconds) {
        showAlert('Please fill out all schedule fields.', 'warning');
        return;
    }

    try {
        await fetch(`/api/presets/${selectedPresetId}/schedules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(scheduleData)
        });
        showAlert('Schedule added successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('addScheduleModal')).hide();
        await loadAndDisplayPresets(); // Refresh data
        selectPreset(selectedPresetId); // Re-select to show the new schedule
    } catch (error) {
        console.error('Error saving schedule:', error);
        showAlert('Failed to save schedule.', 'danger');
    }
}

async function deleteSchedule(scheduleId) {
    if (!confirm('Are you sure you want to delete this schedule?')) return;

    try {
        await fetch(`/api/schedules/${scheduleId}`, { method: 'DELETE' });
        showAlert('Schedule deleted successfully.', 'success');
        await loadAndDisplayPresets(); // Refresh data
        selectPreset(selectedPresetId); // Re-select to show updated schedule list
    } catch (error) {
        console.error('Error deleting schedule:', error);
        showAlert('Failed to delete schedule.', 'danger');
    }
}

// --- PUMP & SENSOR UI UPDATES ---

async function manualPumpControl(action) {
    try {
        const response = await fetch(`/api/irrigation/pump/${action}`, { method: 'POST' });
        const data = await response.json();
        showAlert(data.message, data.status);
    } catch (error) {
        console.error(`Failed to ${action} pump:`, error);
        showAlert(`Error: Could not ${action} pump.`, 'danger');
    }
}

async function updatePumpStatus() {
    try {
        const response = await fetch('/api/irrigation/pump/status');
        if (response.ok) {
            const data = await response.json();
            updatePumpStatusUI(data);
        }
    } catch (error) {
        console.error('Failed to fetch pump status:', error);
    }
}

function updatePumpStatusUI(data) {
    const pumpStatusEl = document.getElementById('pump-status');
    const runningTimeEl = document.getElementById('running-time');
    
    if (data.running) {
        pumpStatusEl.textContent = 'Running';
        pumpStatusEl.className = 'badge bg-success';
        runningTimeEl.textContent = Math.round(data.duration);
    } else {
        pumpStatusEl.textContent = 'Stopped';
        pumpStatusEl.className = 'badge bg-danger';
        runningTimeEl.textContent = '0';
    }
}

function updateSensorReadings(data) {
    const toFixed = (val) => (val !== null && val !== undefined) ? val.toFixed(2) : '--';
    document.getElementById('temp').textContent = toFixed(data.temperature);
    document.getElementById('humidity').textContent = toFixed(data.humidity);
    document.getElementById('soil-moisture').textContent = toFixed(data.soil_moisture);
    document.getElementById('pressure').textContent = toFixed(data.pressure);
    document.getElementById('light-percentage').textContent = toFixed(data.light);
    document.getElementById('rain-percentage').textContent = toFixed(data.rain);
}

function updateSensorStatuses(statuses) {
    for (const sensorName in statuses) {
        const badge = document.getElementById(`${sensorName}-status`);
        if (badge) {
            const status = statuses[sensorName];
            badge.textContent = status;
            badge.className = status === 'Connected' ? 'badge bg-success' : 'badge bg-danger';
        }
    }
}

function updateActivePresetUI() {
    const activePresetEl = document.getElementById('current-preset');
    if (activePreset) {
        activePresetEl.textContent = activePreset.name;
        activePresetEl.className = 'fw-bold text-success';
    } else {
        activePresetEl.textContent = 'None';
        activePresetEl.className = 'fw-bold text-muted';
    }
}

// --- MODALS ---

function openPresetModal(presetId = null) {
    const modalEl = document.getElementById('addPresetModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const preset = presetId ? presets.find(p => p.id === presetId) : null;
    
    document.getElementById('addPresetModalLabel').textContent = preset ? 'Edit Preset' : 'Add New Preset';
    document.getElementById('presetId').value = preset ? preset.id : '';
    document.getElementById('presetName').value = preset ? preset.name : '';
    document.getElementById('presetDescriptionInput').value = preset ? preset.description || '' : '';
    
    modal.show();
}

function openScheduleModal() {
    const modalEl = document.getElementById('addScheduleModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    
    document.getElementById('addScheduleForm').reset();
    modal.show();
}

// --- UTILITY ---
function showAlert(message, type = 'info') {
    const container = document.getElementById('alerts-container');
    if (!container) {
        console.error('Alerts container not found!');
        return;
    }
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    
    container.appendChild(alertDiv);
    
    setTimeout(() => {
        const alertInstance = bootstrap.Alert.getOrCreateInstance(alertDiv);
        if (alertInstance) {
            alertInstance.close();
        }
    }, 5000);
}

// Make functions globally available for inline event handlers (e.g., onclick)
window.deleteSchedule = deleteSchedule;
window.generateReport = generateReport;
window.downloadReport = downloadReport;
window.clearReports = clearReports;

// --- REPORTS ---
document.getElementById('report-type').addEventListener('change', function () {
    const isWeather = this.value === 'weather';
    document.getElementById('weather-options').style.display = isWeather ? 'block' : 'none';
    document.getElementById('irrigation-options').style.display = isWeather ? 'none' : 'block';
});

function getReportOptions() {
    const type = document.getElementById('report-type').value;
    const optionsDivId = type === 'weather' ? 'weather-options' : 'irrigation-options';
    const checkboxes = document.querySelectorAll(`#${optionsDivId} .form-check-input`);
    const columns = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.id.replace(`${type}-`, '').replace('-', '_')); // e.g., weather-soil-moisture -> soil_moisture
    return columns;
}

async function generateReport() {
    const reportData = {
        type: document.getElementById('report-type').value,
        start_date: document.getElementById('report-start-date').value,
        end_date: document.getElementById('report-end-date').value,
        columns: getReportOptions()
    };

    try {
        const response = await fetch('/reports/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reportData)
        });
        const result = await response.json();
        displayReport(result.data, reportData.columns);
    } catch (error) {
        console.error('Error generating report:', error);
        showAlert('Failed to generate report.', 'danger');
    }
}

async function downloadReport() {
    const reportData = {
        type: document.getElementById('report-type').value,
        start_date: document.getElementById('report-start-date').value,
        end_date: document.getElementById('report-end-date').value,
        columns: getReportOptions()
    };

    try {
        const response = await fetch('/reports/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reportData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to download report');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportData.type}_report.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        showAlert('Report downloaded.', 'success');
    } catch (error) {
        console.error('Error downloading report:', error);
        showAlert(error.message, 'danger');
    }
}


function displayReport(data, columns) {
    const displayDiv = document.getElementById('report-display');
    if (!data || data.length === 0) {
        displayDiv.innerHTML = '<p class="text-muted">No data available for the selected criteria.</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'table table-striped table-bordered mt-3';

    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const displayColumns = ['timestamp', ...columns];
    displayColumns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); // Format for display
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    data.forEach(item => {
        const row = document.createElement('tr');
        displayColumns.forEach(col => {
            const td = document.createElement('td');
            let value = item[col];
            // Format timestamp for readability
            if (col === 'timestamp') {
                value = new Date(value).toLocaleString();
            }
            td.textContent = value !== null && value !== undefined ? value : 'N/A';
            row.appendChild(td);
        });
        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    displayDiv.innerHTML = '';
    displayDiv.appendChild(table);
}

function clearReports() {
    document.getElementById('report-display').innerHTML = '';
    showAlert('Report display cleared.', 'info');
}