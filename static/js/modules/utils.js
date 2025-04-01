// Utils Module - Utility functions used across the application

// Function to format a date as YYYY-MM-DD
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Function to format a time as HH:MM:SS
function formatTime(date) {
    return date.toTimeString().split(' ')[0];
}

// Function to format a timestamp for display
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return `${formatDate(date)} ${formatTime(date)}`;
}

// Function to validate a form
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form with ID ${formId} not found`);
        return false;
    }
    
    return form.checkValidity();
}

// Export functions
window.formatDate = formatDate;
window.formatTime = formatTime;
window.formatTimestamp = formatTimestamp;
window.validateForm = validateForm;