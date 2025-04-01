// Presets Module - Handles preset management

// Function to load presets from the server
function loadPresets() {
    fetch('/api/irrigation/presets')
        .then(response => response.json())
        .then(data => {
            const presetsList = document.getElementById('presetsList');
            if (!presetsList) {
                console.error('Presets list container not found');
                return;
            }
            
            presetsList.innerHTML = '';
            
            if (data.length === 0) {
                presetsList.innerHTML = '<div class="col-12"><p class="text-muted">No presets available</p></div>';
                return;
            }
            
            // Create a table for presets
            let tableHTML = `
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Description</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.forEach(preset => {
                tableHTML += `
                    <tr data-preset-id="${preset.id}">
                        <td>${preset.name}</td>
                        <td>${preset.description || 'No description'}</td>
                        <td>
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-primary activate-preset-btn" title="Activate">
                                    <i class="fas fa-play"></i>
                                </button>
                                <button class="btn btn-info view-preset-btn" title="View Details">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-danger delete-preset-btn" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            tableHTML += `
                    </tbody>
                </table>
            `;
            
            presetsList.innerHTML = tableHTML;
            
            // Add event listeners to buttons
            document.querySelectorAll('.activate-preset-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent row click
                    const presetId = e.target.closest('tr').dataset.presetId;
                    activatePreset(presetId);
                });
            });
            
            document.querySelectorAll('.view-preset-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent row click
                    const presetId = e.target.closest('tr').dataset.presetId;
                    showPresetDetails(presetId);
                });
            });
            
            document.querySelectorAll('.delete-preset-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent row click
                    const presetId = e.target.closest('tr').dataset.presetId;
                    deletePreset(presetId);
                });
            });
            
            // Make entire row clickable to view details
            document.querySelectorAll('#presetsList tr[data-preset-id]').forEach(row => {
                row.addEventListener('click', () => {
                    const presetId = row.dataset.presetId;
                    showPresetDetails(presetId);
                });
            });
            
            console.log(`Loaded ${data.length} presets`);
        })
        .catch(error => {
            console.error('Error loading presets:', error);
            const presetsList = document.getElementById('presetsList');
            if (presetsList) {
                presetsList.innerHTML = '<div class="col-12"><p class="text-danger">Error loading presets</p></div>';
            }
        });
}

// Function to save a new preset
function saveNewPreset() {
    const presetNameInput = document.getElementById('presetName');
    
    if (!presetNameInput) {
        console.error('Preset name input not found');
        return;
    }
    
    const presetName = presetNameInput.value.trim();
    
    if (!presetName) {
        alert('Please enter a preset name');
        return;
    }
    
    // Get description if it exists
    const presetDescriptionInput = document.getElementById('presetDescription');
    const presetDescription = presetDescriptionInput ? presetDescriptionInput.value.trim() : '';
    
    const presetData = {
        name: presetName,
        description: presetDescription,
        schedules: [] // New preset starts with no schedules
    };
    
    fetch('/api/irrigation/preset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(presetData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Preset created:', data);
        if (window.addPresetModal) {
            addPresetModal.hide();
        }
        
        // Clear form fields
        presetNameInput.value = '';
        if (presetDescriptionInput) {
            presetDescriptionInput.value = '';
        }
        
        // Show success message
        showAlert('Preset created successfully', 'success');
        
        // Reload presets
        loadPresets();
    })
    .catch(error => {
        console.error('Error creating preset:', error);
        showAlert('Error creating preset. Please try again.', 'danger');
    });
}

// Function to show preset details
function showPresetDetails(presetId) {
    if (!presetId) {
        console.error('No preset ID provided');
        return;
    }
    
    fetch(`/api/irrigation/preset/${presetId}`)
        .then(response => response.json())
        .then(data => {
            console.log('Preset details:', data);
            
            const presetDetails = document.getElementById('presetDetails');
            if (!presetDetails) {
                console.error('Preset details container not found');
                return;
            }
            
            // Enable the Add Schedule button and set the preset ID
            const addScheduleBtn = document.getElementById('addScheduleBtn');
            if (addScheduleBtn) {
                addScheduleBtn.disabled = false;
                addScheduleBtn.dataset.presetId = presetId;
            }
            
            // Create details HTML
            let detailsHTML = `
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">${data.name}</h5>
                        <p class="text-muted mb-0 small">${data.description || 'No description'}</p>
                    </div>
                    <div class="card-body">
                        <h6>Schedules</h6>
                        <div id="schedulesList">
            `;
            
            if (!data.schedules || data.schedules.length === 0) {
                detailsHTML += '<p class="text-muted">No schedules for this preset</p>';
            } else {
                detailsHTML += '<div class="list-group">';
                data.schedules.forEach(schedule => {
                    detailsHTML += `
                        <div class="list-group-item list-group-item-action">
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1">Start Time: ${schedule.start_time}</h6>
                                <small>Duration: ${schedule.duration} seconds</small>
                            </div>
                            <div class="d-flex justify-content-end mt-2">
                                <button class="btn btn-sm btn-primary me-2 edit-schedule-btn" data-schedule-id="${schedule.id}">
                                    <i class="fas fa-edit"></i> Edit
                                </button>
                                <button class="btn btn-sm btn-danger delete-schedule-btn" data-schedule-id="${schedule.id}">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </div>
                        </div>
                    `;
                });
                detailsHTML += '</div>';
            }
            
            detailsHTML += `
                        </div>
                    </div>
                </div>
            `;
            
            presetDetails.innerHTML = detailsHTML;
            
            // Add event listeners for schedule buttons
            document.querySelectorAll('.edit-schedule-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const scheduleId = btn.dataset.scheduleId;
                    editSchedule(scheduleId);
                });
            });
            
            document.querySelectorAll('.delete-schedule-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const scheduleId = btn.dataset.scheduleId;
                    deleteSchedule(scheduleId);
                });
            });
            
            // Highlight the selected preset in the list
            document.querySelectorAll('#presetsList tr').forEach(row => {
                row.classList.remove('table-active');
                if (row.dataset.presetId === presetId) {
                    row.classList.add('table-active');
                }
            });
        })
        .catch(error => {
            console.error('Error loading preset details:', error);
            showAlert('Error loading preset details', 'danger');
        });
}

// Function to activate a preset
function activatePreset(presetId) {
    if (!presetId) {
        console.error('No preset ID provided');
        return;
    }
    
    fetch(`/api/irrigation/preset/${presetId}/activate`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Server error: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        console.log('Preset activated:', data);
        
        // Update the current preset display
        const currentPresetElement = document.getElementById('current-preset');
        if (currentPresetElement) {
            currentPresetElement.textContent = data.name;
        }
        
        // Show success message
        showAlert('Preset activated successfully', 'success');
    })
    .catch(error => {
        console.error('Error activating preset:', error);
        showAlert('Error activating preset', 'danger');
    });
}

// Function to delete a preset
function deletePreset(presetId) {
    if (!presetId) {
        console.error('No preset ID provided');
        return;
    }
    
    if (confirm('Are you sure you want to delete this preset? This action cannot be undone.')) {
        fetch(`/api/irrigation/preset/${presetId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Preset deleted:', data);
            showAlert('Preset deleted successfully', 'success');
            
            // Clear preset details if this was the selected preset
            const addScheduleBtn = document.getElementById('addScheduleBtn');
            if (addScheduleBtn && addScheduleBtn.dataset.presetId === presetId) {
                const presetDetails = document.getElementById('presetDetails');
                if (presetDetails) {
                    presetDetails.innerHTML = '<div class="text-center text-muted py-3"><p>Select a preset to view details</p></div>';
                }
                addScheduleBtn.disabled = true;
                delete addScheduleBtn.dataset.presetId;
            }
            
            // Reload presets list
            loadPresets();
        })
        .catch(error => {
            console.error('Error deleting preset:', error);
            showAlert('Error deleting preset', 'danger');
        });
    }
}

// Helper function to get the selected preset ID
function getSelectedPresetId() {
    const addScheduleBtn = document.getElementById('addScheduleBtn');
    return addScheduleBtn ? addScheduleBtn.dataset.presetId : null;
}

// Export functions
window.loadPresets = loadPresets;
window.saveNewPreset = saveNewPreset;
window.showPresetDetails = showPresetDetails;
window.activatePreset = activatePreset;
window.deletePreset = deletePreset;
window.getSelectedPresetId = getSelectedPresetId;