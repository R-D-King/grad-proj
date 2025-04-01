// Events Module - Handles UI event listeners

// Set up UI event listeners
function setupEventListeners() {
    // Manual pump control
    const manualOnBtn = document.getElementById('manual-on-btn');
    if (manualOnBtn) {
        manualOnBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to start the pump?')) {
                fetch('/api/irrigation/pump/start', { method: 'POST' });
            }
        });
    }
    
    const manualOffBtn = document.getElementById('manual-off-btn');
    if (manualOffBtn) {
        manualOffBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to stop the pump?')) {
                fetch('/api/irrigation/pump/stop', { method: 'POST' });
            }
        });
    }
    
    // Preset management
    const addPresetBtn = document.getElementById('addPresetBtn');
    if (addPresetBtn) {
        addPresetBtn.addEventListener('click', () => addPresetModal.show());
    }
    
    const savePresetBtn = document.getElementById('savePresetBtn');
    if (savePresetBtn) {
        savePresetBtn.addEventListener('click', saveNewPreset);
    }
    
    // Schedule management
    const addScheduleBtn = document.getElementById('addScheduleBtn');
    if (addScheduleBtn) {
        addScheduleBtn.addEventListener('click', () => addScheduleModal.show());
    }
    
    const saveScheduleBtn = document.getElementById('saveScheduleBtn');
    if (saveScheduleBtn) {
        saveScheduleBtn.addEventListener('click', saveNewSchedule);
    }
    
    const updateScheduleBtn = document.getElementById('updateScheduleBtn');
    if (updateScheduleBtn) {
        updateScheduleBtn.addEventListener('click', updateSchedule);
    }
    
    // Report buttons
    const generateReportBtn = document.getElementById('generateReportBtn');
    if (generateReportBtn) {
        generateReportBtn.addEventListener('click', generateReport);
    }
    
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    if (downloadReportBtn) {
        downloadReportBtn.addEventListener('click', downloadReport);
    }
    
    const clearReportBtn = document.getElementById('clearReportBtn');
    if (clearReportBtn) {
        clearReportBtn.addEventListener('click', clearReports);
    }
    
    // Set up the report type change listener
    const reportTypeSelect = document.getElementById('report-type');
    if (reportTypeSelect) {
        reportTypeSelect.addEventListener('change', toggleReportOptions);
        
        // Call it once to set initial state
        toggleReportOptions();
        console.log('Set up report type change listener');
    }
}

// Export function
window.setupEventListeners = setupEventListeners;