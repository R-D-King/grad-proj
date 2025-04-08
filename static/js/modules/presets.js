// Presets Module - Handles preset management

// Function to load presets from the server
// Update the loadPresets function to properly display presets
function loadPresets() {
    console.log('Loading presets... (NEW IMPLEMENTATION)');

    // Get the presets list container
    const presetsList = document.getElementById('presetsList');
    if (!presetsList) {
        console.error('Presets list container not found!');
        return;
    }

    // Clear any existing content
    presetsList.innerHTML = '<div class="col-12 text-center"><p>Loading presets...</p></div>';

    // Fetch presets from the API
    fetch('/api/irrigation/presets')
        .then(response => {
            console.log('Presets API response status:', response.status);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            return response.json();
        })
        .then(presets => {
            console.log('Received presets data:', presets);

            // Clear the loading message
            presetsList.innerHTML = '';

            // Check if we have any presets
            if (!presets || !Array.isArray(presets) || presets.length === 0) {
                console.log('No presets available');
                presetsList.innerHTML = '<div class="col-12 text-center"><p class="text-muted">No presets available</p></div>';
                return;
            }

            console.log(`Found ${presets.length} presets, rendering...`);

            // Render each preset as a simple card
            presets.forEach(preset => {
                console.log(`Rendering preset: ${preset.id} - ${preset.name}`);

                // Create a div for the preset
                const presetCard = document.createElement('div');
                presetCard.className = 'col-md-6 mb-3';
                presetCard.innerHTML = `
                    <div class="card h-100 preset-card ${preset.active ? 'active' : ''}" data-preset-id="${preset.id}">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title mb-3">${preset.name}</h5>
                            <div class="preset-info">
                                <p class="card-text mb-2">
                                    <i class="fas fa-clock me-2 text-primary"></i>
                                    <span class="text-muted">Duration:</span> ${preset.duration}s
                                </p>
                                <p class="card-text mb-0">
                                    <i class="fas fa-water me-2 text-primary"></i>
                                    <span class="text-muted">Water Level:</span> ${preset.water_level}%
                                </p>
                            </div>
                            <div class="mt-auto pt-3 d-flex justify-content-between align-items-center">
                                <span class="badge ${preset.active ? 'bg-success' : 'bg-secondary'} rounded-pill">
                                    ${preset.active ? 'Active' : 'Inactive'}
                                </span>
                                <button class="btn btn-sm btn-outline-primary add-schedule-btn" data-preset-id="${preset.id}">
                                    <i class="fas fa-calendar-plus"></i> Schedule
                                </button>
                            </div>
                        </div>
                    </div>
                `;

                // Add the preset card to the list
                presetsList.appendChild(presetCard);
                console.log(`Added preset card to DOM: ${preset.id}`);
            });

            // Add click event to the preset cards
            document.querySelectorAll('.preset-card').forEach(card => {
                card.addEventListener('click', function (e) {
                    // Don't trigger if clicking on a button inside the card
                    if (e.target.closest('button')) {
                        return;
                    }
                    
                    const presetId = this.dataset.presetId;
                    console.log(`Preset card clicked: ${presetId}`);

                    // Remove active class from all cards
                    document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active'));

                    // Add active class to this card
                    this.classList.add('active');

                    // Store the selected preset ID for use with the Add Schedule button
                    const addScheduleBtn = document.querySelector('.btn.btn-primary.rounded-pill');
                    if (addScheduleBtn) {
                        addScheduleBtn.dataset.presetId = presetId;
                        // Make sure the button is enabled
                        addScheduleBtn.disabled = false;
                    }

                    // Show preset details
                    showPresetDetails(presetId);
                });
            });

            // Add click events to delete buttons
            document.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', function () {
                    const presetId = this.dataset.presetId;
                    console.log(`Delete button clicked for preset: ${presetId}`);
                    deletePreset(presetId);
                });
            });

            console.log('Presets loaded and rendered successfully');
        })
        .catch(error => {
            console.error('Error loading presets:', error);
            presetsList.innerHTML = '<div class="col-12 text-center"><p class="text-danger">Error loading presets</p></div>';
        });
}

// Add this near the top of your file
// Add custom styles for preset cards
function addPresetStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .preset-card {
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(0,0,0,0.1);
            background: #ffffff;
        }
        .preset-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        .preset-card.active {
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2);
            background: rgba(0, 123, 255, 0.02);
        }
        .btn-icon {
            padding: 0.25rem;
            line-height: 1;
            border-radius: 0.2rem;
        }
        .preset-info {
            padding: 0.5rem;
            background: rgba(0,0,0,0.02);
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .schedule-item {
            border: 1px solid #eee;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 10px;
        }
    `;
    document.head.appendChild(style);
    console.log('Added custom styles for presets');
}

// Call this function early in initialization
addPresetStyles();

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

    // Update the endpoint to match the backend route
    fetch('/api/irrigation/presets', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(presetData)
    })
        .then(response => response.json())
        .then(data => {
            console.log('Preset created:', data);

            // Close the modal using Bootstrap's API
            const modalElement = document.getElementById('addPresetModal');
            if (modalElement) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                } else {
                    // If the instance doesn't exist yet, create it and then hide
                    const newModal = new bootstrap.Modal(modalElement);
                    newModal.hide();
                }
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

    console.log('Fetching preset details for ID:', presetId);

    // Fix the URL - add a slash before the ID
    fetch(`/api/irrigation/presets/${presetId}`)
        .then(response => {
            console.log('Preset details response status:', response.status);
            if (!response.ok) {
                console.error(`Error response from server: ${response.status}`);
                throw new Error(`Server returned ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Preset details data:', data);

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

            // Display preset details
            presetDetails.innerHTML = `
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${data.name}</h6>
                        <div>
                            <button class="btn btn-sm btn-primary activate-preset-btn" data-preset-id="${data.id}">
                                <i class="fas fa-play"></i> Activate
                            </button>
                            <button class="btn btn-sm btn-danger delete-preset-btn" data-preset-id="${data.id}">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <p><strong>Duration:</strong> ${data.duration} seconds</p>
                        <p><strong>Water Level:</strong> ${data.water_level}%</p>
                        <p><strong>Auto Start:</strong> ${data.auto_start ? 'Yes' : 'No'}</p>
                        <p><strong>Active:</strong> ${data.active ? 'Yes' : 'No'}</p>
                        <p><strong>Created:</strong> ${new Date(data.created_at).toLocaleString()}</p>
                        
                        <h6 class="mt-4">Schedules</h6>
                        <div id="schedulesList">
                            ${data.schedules && data.schedules.length > 0
                    ? data.schedules.map(schedule => `
                                    <div class="schedule-item">
                                        <p><strong>Day:</strong> ${schedule.day_of_week}</p>
                                        <p><strong>Time:</strong> ${schedule.time}</p>
                                        <button class="btn btn-sm btn-danger delete-schedule-btn" 
                                                data-schedule-id="${schedule.id}">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    </div>
                                `).join('')
                    : '<p class="text-muted">No schedules set</p>'
                }
                        </div>
                    </div>
                </div>
            `;

            console.log('Preset details rendered successfully');

            // Add event listeners to buttons in the details view
            const activateBtn = presetDetails.querySelector('.activate-preset-btn');
            if (activateBtn) {
                activateBtn.addEventListener('click', function () {
                    activatePreset(this.dataset.presetId);
                });
            }

            const deleteBtn = presetDetails.querySelector('.delete-preset-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', function () {
                    // Make sure we're calling the correct deletePreset function
                    // that uses the plural 'presets' in the URL
                    deletePreset(this.dataset.presetId);
                });
            }

            // Add event listeners to delete schedule buttons
            const deleteScheduleBtns = presetDetails.querySelectorAll('.delete-schedule-btn');
            deleteScheduleBtns.forEach(btn => {
                btn.addEventListener('click', function () {
                    deleteSchedule(this.dataset.scheduleId);
                });
            });
        })
        .catch(error => {
            console.error('Error loading preset details:', error);
            const presetDetails = document.getElementById('presetDetails');
            if (presetDetails) {
                presetDetails.innerHTML = '<div class="alert alert-danger">Error loading preset details</div>';
            }
        });
}

// Function to activate a preset
function activatePreset(presetId) {
    if (!presetId) {
        console.error('No preset ID provided');
        return;
    }

    // Update the endpoint to match the backend route - change to plural form
    fetch(`/api/irrigation/presets/${presetId}/activate`, {
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
        // Add debug logging to see the exact URL being used
        const deleteUrl = `/api/irrigation/presets/${presetId}`;
        console.log('Deleting preset with URL:', deleteUrl);
        
        // Update the endpoint to use the plural form 'presets' instead of 'preset'
        fetch(deleteUrl, {
            method: 'DELETE'
        })
            .then(response => {
                console.log('Delete response status:', response.status);
                return response.json();
            })
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


function showAlert(message, type) {
    const alertsContainer = document.getElementById('alerts-container') || document.createElement('div');

    if (!document.getElementById('alerts-container')) {
        alertsContainer.id = 'alerts-container';
        alertsContainer.className = 'position-fixed top-0 end-0 p-3';
        document.body.appendChild(alertsContainer);
    }

    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    alertsContainer.innerHTML += alertHTML;

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

// Update the initialization function
function initializePresetUI() {
    console.log('Initializing preset UI components (DEBUGGING)');

    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded! Modal functionality will not work.');
    } else {
        console.log('Bootstrap is available');
    }

    // Set up the Add Preset button
    const addPresetBtn = document.getElementById('addPresetBtn');
    console.log('Add Preset button:', addPresetBtn);

    if (addPresetBtn) {
        console.log('Setting up Add Preset button');
        // Make sure we're using Bootstrap's modal API
        addPresetBtn.setAttribute('data-bs-toggle', 'modal');
        addPresetBtn.setAttribute('data-bs-target', '#addPresetModal');
    } else {
        console.error('Add Preset button not found!');
    }

    // Set up the Save Preset button in the modal
    const savePresetBtn = document.getElementById('savePresetBtn');
    console.log('Save Preset button:', savePresetBtn);

    if (savePresetBtn) {
        console.log('Setting up Save Preset button');
        // Remove any existing event listeners by cloning the button
        const newSaveBtn = savePresetBtn.cloneNode(true);
        savePresetBtn.parentNode.replaceChild(newSaveBtn, savePresetBtn);

        // Add the event listener to the new button
        newSaveBtn.addEventListener('click', function () {
            console.log('Save Preset button clicked');
            saveNewPreset();
        });
    } else {
        console.error('Save Preset button not found!');
    }

    // Check if the presets list container exists
    const presetsList = document.getElementById('presetsList');
    console.log('Presets list container:', presetsList);

    if (!presetsList) {
        console.error('Presets list container not found! Check your HTML.');
    }

    // Load presets immediately
    console.log('Loading presets...');
    setTimeout(() => {
        console.log('Forcing presets to load...');
        loadPresets();
    }, 500);
}

// Make sure we only have one initialization point
// Fix the initialization code - remove the invalid selector
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOMContentLoaded event fired - Initializing presets module');

    // Only call one initialization function
    initPresetsModule();
    
    // Remove these duplicate calls
    // initializePresetUI();
    // setTimeout(loadPresets, 100);
});

// Remove or comment out these duplicate event listeners
// document.addEventListener('DOMContentLoaded', function () {
//     console.log('DOM ready - Loading presets directly');
//     setTimeout(loadPresets, 100); // Short delay to ensure DOM is fully ready
// });

// Also add a fallback in case DOMContentLoaded already fired
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    console.log('Document already loaded - Loading presets directly');
    setTimeout(initPresetsModule, 100);
}

// Function to initialize the presets module
function initPresetsModule() {
    console.log('Initializing presets module...');
    
    // Load presets on page load
    loadPresets();
    
    // Set up the Add Preset button
    const addPresetBtn = document.getElementById('addPresetBtn');
    if (addPresetBtn) {
        console.log('Setting up Add Preset button');
        // Make sure we're using Bootstrap's modal API
        addPresetBtn.setAttribute('data-bs-toggle', 'modal');
        addPresetBtn.setAttribute('data-bs-target', '#addPresetModal');
    }
    
    // Set up the Save Preset button in the modal
    const savePresetBtn = document.getElementById('savePresetBtn');
    if (savePresetBtn) {
        // Remove any existing event listeners by cloning the button
        const newSaveBtn = savePresetBtn.cloneNode(true);
        savePresetBtn.parentNode.replaceChild(newSaveBtn, savePresetBtn);
        
        // Add the event listener to the new button
        newSaveBtn.addEventListener('click', function () {
            console.log('Save Preset button clicked');
            saveNewPreset();
        });
    }
    
    // Add event listener to the Add Schedule button (the one with the plus icon)
    const addScheduleBtn = document.querySelector('.btn.btn-primary.rounded-pill');
    if (addScheduleBtn) {
        console.log('Found Add Schedule button:', addScheduleBtn);
        
        // Make sure the button is not disabled by default
        addScheduleBtn.disabled = false;
        
        // Add the event listener to the button
        addScheduleBtn.addEventListener('click', function() {
            console.log('Add Schedule button clicked');
            const presetId = getSelectedPresetId();
            if (!presetId) {
                showAlert('Please select a preset first', 'warning');
                return;
            }
            
            // Open the schedule modal for the selected preset
            openScheduleModal(presetId);
        });
    }
}

// Remove the initializePresetUI function since we're consolidating everything in initPresetsModule
// function initializePresetUI() { ... }

// Call the init function when the DOM is loaded - make sure this is the only call
document.addEventListener('DOMContentLoaded', function() {
    // Remove all other initialization code and just call this one function
    initPresetsModule();
});

// Function to load presets from the server
function loadPresets() {
    console.log('Loading presets...');
    fetch('/api/irrigation/presets')
        .then(response => response.json())
        .then(data => {
            renderPresets(data);
            setupEventListeners();
        })
        .catch(error => {
            console.error('Error loading presets:', error);
            showAlert('Error loading presets', 'danger');
        });
}

// Function to set up all event listeners after presets are loaded
function setupEventListeners() {
    // Set up preset card click events
    document.querySelectorAll('.preset-card').forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on a button inside the card
            if (e.target.closest('button')) {
                return;
            }
            
            const presetId = this.dataset.presetId;
            console.log(`Preset card clicked: ${presetId}`);
            
            // Remove active class from all cards
            document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active'));
            
            // Add active class to this card
            this.classList.add('active');
            
            // Show preset details
            showPresetDetails(presetId);
            
            // Enable the Add Schedule button
            const addScheduleBtn = document.querySelector('.btn.btn-primary.rounded-pill');
            if (addScheduleBtn) {
                addScheduleBtn.disabled = false;
                addScheduleBtn.dataset.presetId = presetId;
            }
        });
    });
    
    // Set up Add Schedule button
    const addScheduleBtn = document.querySelector('.btn.btn-primary.rounded-pill');
    if (addScheduleBtn) {
        console.log('Setting up Add Schedule button');
        
        // Initially disable the button until a preset is selected
        addScheduleBtn.disabled = true;
        
        addScheduleBtn.addEventListener('click', function() {
            const presetId = this.dataset.presetId;
            if (!presetId) {
                showAlert('Please select a preset first', 'warning');
                return;
            }
            
            openScheduleModal(presetId);
        });
    }
    
    // Set up Save Schedule button in the modal
    const saveScheduleBtn = document.getElementById('saveScheduleBtn');
    if (saveScheduleBtn) {
        saveScheduleBtn.addEventListener('click', saveSchedule);
    }
}

// Function to open the schedule modal
function openScheduleModal(presetId) {
    console.log(`Opening schedule modal for preset: ${presetId}`);
    
    // Get the preset details
    fetch(`/api/irrigation/presets/${presetId}`)
        .then(response => response.json())
        .then(preset => {
            // Set the preset ID and name in the modal
            const scheduleModal = document.getElementById('scheduleModal');
            const presetNameElement = scheduleModal.querySelector('#schedulePresetName');
            const presetIdInput = scheduleModal.querySelector('#schedulePresetId');
            
            if (presetNameElement) presetNameElement.textContent = preset.name;
            if (presetIdInput) presetIdInput.value = presetId;
            
            // Show the modal
            const modal = new bootstrap.Modal(scheduleModal);
            modal.show();
        })
        .catch(error => {
            console.error('Error fetching preset details:', error);
            showAlert('Error opening schedule modal', 'danger');
        });
}

// Function to save a new schedule
function saveSchedule() {
    const presetId = document.getElementById('schedulePresetId').value;
    const dayOfWeek = document.getElementById('scheduleDayOfWeek').value;
    const time = document.getElementById('scheduleTime').value;
    const duration = document.getElementById('scheduleDuration').value;
    
    if (!presetId || !dayOfWeek || !time || !duration) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }
    
    // Create the schedule data
    const scheduleData = {
        preset_id: presetId,
        day_of_week: dayOfWeek,
        time: time,
        duration: parseInt(duration)
    };
    
    // Send the data to the server
    fetch('/api/irrigation/schedule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(scheduleData)
    })
        .then(response => response.json())
        .then(data => {
            console.log('Schedule created:', data);
            
            // Close the modal
            const scheduleModal = document.getElementById('scheduleModal');
            const modal = bootstrap.Modal.getInstance(scheduleModal);
            if (modal) modal.hide();
            
            // Show success message
            showAlert('Schedule created successfully', 'success');
            
            // Refresh the preset details
            showPresetDetails(presetId);
        })
        .catch(error => {
            console.error('Error creating schedule:', error);
            showAlert('Error creating schedule', 'danger');
        });
}

// Make these functions available globally
window.openScheduleModal = openScheduleModal;
window.saveSchedule = saveSchedule;

// Single initialization point
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing presets');
    loadPresets();
    
    // Set up the Add Preset button
    const addPresetBtn = document.getElementById('addPresetBtn');
    if (addPresetBtn) {
        console.log('Setting up Add Preset button');
        addPresetBtn.setAttribute('data-bs-toggle', 'modal');
        addPresetBtn.setAttribute('data-bs-target', '#addPresetModal');
    }
    
    // Set up the Save Preset button in the modal
    const savePresetBtn = document.getElementById('savePresetBtn');
    if (savePresetBtn) {
        savePresetBtn.addEventListener('click', saveNewPreset);
    }
});

function showAlert(message, type) {
    const alertsContainer = document.getElementById('alerts-container') || document.createElement('div');

    if (!document.getElementById('alerts-container')) {
        alertsContainer.id = 'alerts-container';
        alertsContainer.className = 'position-fixed top-0 end-0 p-3';
        document.body.appendChild(alertsContainer);
    }

    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    alertsContainer.innerHTML += alertHTML;

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

// Update the initialization function
function initializePresetUI() {
    console.log('Initializing preset UI components (DEBUGGING)');

    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded! Modal functionality will not work.');
    } else {
        console.log('Bootstrap is available');
    }

    // Set up the Add Preset button
    const addPresetBtn = document.getElementById('addPresetBtn');
    console.log('Add Preset button:', addPresetBtn);

    if (addPresetBtn) {
        console.log('Setting up Add Preset button');
        // Make sure we're using Bootstrap's modal API
        addPresetBtn.setAttribute('data-bs-toggle', 'modal');
        addPresetBtn.setAttribute('data-bs-target', '#addPresetModal');
    } else {
        console.error('Add Preset button not found!');
    }

    // Set up the Save Preset button in the modal
    const savePresetBtn = document.getElementById('savePresetBtn');
    console.log('Save Preset button:', savePresetBtn);

    if (savePresetBtn) {
        console.log('Setting up Save Preset button');
        // Remove any existing event listeners by cloning the button
        const newSaveBtn = savePresetBtn.cloneNode(true);
        savePresetBtn.parentNode.replaceChild(newSaveBtn, savePresetBtn);

        // Add the event listener to the new button
        newSaveBtn.addEventListener('click', function () {
            console.log('Save Preset button clicked');
            saveNewPreset();
        });
    } else {
        console.error('Save Preset button not found!');
    }

    // Check if the presets list container exists
    const presetsList = document.getElementById('presetsList');
    console.log('Presets list container:', presetsList);

    if (!presetsList) {
        console.error('Presets list container not found! Check your HTML.');
    }

    // Load presets immediately
    console.log('Loading presets...');
    setTimeout(() => {
        console.log('Forcing presets to load...');
        loadPresets();
    }, 500);
}

// Make sure we only have one initialization point
// Fix the initialization code - remove the invalid selector
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOMContentLoaded event fired - Initializing presets module');

    // Only call one initialization function
    initPresetsModule();
    
    // Remove these duplicate calls
    // initializePresetUI();
    // setTimeout(loadPresets, 100);
});

// Remove or comment out these duplicate event listeners
// document.addEventListener('DOMContentLoaded', function () {
//     console.log('DOM ready - Loading presets directly');
//     setTimeout(loadPresets, 100); // Short delay to ensure DOM is fully ready
// });

// Also add a fallback in case DOMContentLoaded already fired
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    console.log('Document already loaded - Loading presets directly');
    setTimeout(initPresetsModule, 100);
}

// Function to initialize the presets module
function initPresetsModule() {
    console.log('Initializing presets module...');
    
    // Load presets on page load
    loadPresets();
    
    // Set up the Add Preset button
    const addPresetBtn = document.getElementById('addPresetBtn');
    if (addPresetBtn) {
        console.log('Setting up Add Preset button');
        // Make sure we're using Bootstrap's modal API
        addPresetBtn.setAttribute('data-bs-toggle', 'modal');
        addPresetBtn.setAttribute('data-bs-target', '#addPresetModal');
    }
    
    // Set up the Save Preset button in the modal
    const savePresetBtn = document.getElementById('savePresetBtn');
    if (savePresetBtn) {
        // Remove any existing event listeners by cloning the button
        const newSaveBtn = savePresetBtn.cloneNode(true);
        savePresetBtn.parentNode.replaceChild(newSaveBtn, savePresetBtn);

        // Add the event listener to the new button
        newSaveBtn.addEventListener('click', function () {
            console.log('Save Preset button clicked');
            saveNewPreset();
        });
    }
    
    // Add event listener to the Add Schedule button (the one with the plus icon)
    const addScheduleBtn = document.querySelector('.btn.btn-primary.rounded-pill');
    if (addScheduleBtn) {
        console.log('Found Add Schedule button:', addScheduleBtn);
        
        // Make sure the button is not disabled by default
        addScheduleBtn.disabled = false;
        
        // Add the event listener to the button
        addScheduleBtn.addEventListener('click', function() {
            console.log('Add Schedule button clicked');
            const presetId = getSelectedPresetId();
            if (!presetId) {
                showAlert('Please select a preset first', 'warning');
                return;
            }
            
            // Open the schedule modal for the selected preset
            openScheduleModal(presetId);
        });
    }
}

// Remove the initializePresetUI function since we're consolidating everything in initPresetsModule
// function initializePresetUI() { ... }

// Call the init function when the DOM is loaded - make sure this is the only call
document.addEventListener('DOMContentLoaded', function() {
    // Remove all other initialization code and just call this one function
    initPresetsModule();
});
