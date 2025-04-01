// UI Module - Handles UI initialization and common UI functions

// Initialize Bootstrap modals
function initializeUI() {
    window.addPresetModal = new bootstrap.Modal(document.getElementById('addPresetModal'));
    window.addScheduleModal = new bootstrap.Modal(document.getElementById('addScheduleModal'));
    window.editScheduleModal = new bootstrap.Modal(document.getElementById('editScheduleModal'));
}

// Helper function to show alerts
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) {
        // Create alerts container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'alerts-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }
    
    const id = 'alert-' + Date.now();
    const alertHTML = `
        <div id="${id}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const alertsContainerElement = document.getElementById('alerts-container');
    if (alertsContainerElement) {
        alertsContainerElement.insertAdjacentHTML('beforeend', alertHTML);
    }
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.getElementById(id);
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// Export functions
window.initializeUI = initializeUI;
window.showAlert = showAlert;