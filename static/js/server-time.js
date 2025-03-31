// Server time synchronization - minimal version
document.addEventListener('DOMContentLoaded', function() {
    // Update time display every second
    setInterval(updateTimeDisplay, 1000);
});

// Update the server time display
function updateTimeDisplay() {
    fetch('/api/server-time/display')
        .then(response => response.json())
        .then(data => {
            const timeDisplay = document.getElementById('server-time-display');
            if (timeDisplay) {
                timeDisplay.textContent = data.formatted_time;
                timeDisplay.style.color = ''; // Reset to default color
            }
        })
        .catch(error => {
            console.error('Error getting server time:', error);
            // Display offline message when server is not responding
            const timeDisplay = document.getElementById('server-time-display');
            if (timeDisplay) {
                timeDisplay.textContent = 'Server offline';
                timeDisplay.style.color = 'red'; // Set text color to red
            }
        });
}

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

// Make function available globally
window.checkScheduleTime = checkScheduleTime;