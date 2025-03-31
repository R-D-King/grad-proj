// Server time synchronization
let serverTimeOffset = 0;
let lastSyncTime = 0;

// Function to sync with server time
function syncServerTime() {
    const clientTime = Date.now();
    
    fetch('/api/server-time')
        .then(response => response.json())
        .then(data => {
            // Calculate offset between server and client time
            const serverTime = data.timestamp * 1000; // Convert to milliseconds
            serverTimeOffset = serverTime - clientTime;
            lastSyncTime = clientTime;
            
            console.log(`Time synced with server. Offset: ${serverTimeOffset}ms`);
            
            // Update time display immediately
            updateTimeDisplay();
        })
        .catch(error => {
            console.error('Error syncing time with server:', error);
        });
}

// Get current time adjusted to server time
function getServerAdjustedTime() {
    return new Date(Date.now() + serverTimeOffset);
}

// Update the server time display
function updateTimeDisplay() {
    const serverTime = getServerAdjustedTime();
    const timeDisplay = document.getElementById('server-time-display');
    
    if (timeDisplay) {
        // Format time as HH:MM:SS
        const hours = serverTime.getHours().toString().padStart(2, '0');
        const minutes = serverTime.getMinutes().toString().padStart(2, '0');
        const seconds = serverTime.getSeconds().toString().padStart(2, '0');
        timeDisplay.textContent = `${hours}:${minutes}:${seconds}`;
    }
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initial sync with server
    syncServerTime();
    
    // Update time display every second
    setInterval(updateTimeDisplay, 1000);
    
    // Re-sync with server every 5 minutes to prevent drift
    setInterval(syncServerTime, 5 * 60 * 1000);
});

// Function to check if a schedule should run based on server time
function checkScheduleTime(scheduleTime) {
    const serverTime = getServerAdjustedTime();
    const currentHour = serverTime.getHours().toString().padStart(2, '0');
    const currentMinute = serverTime.getMinutes().toString().padStart(2, '0');
    const currentTimeHHMM = `${currentHour}:${currentMinute}`;
    
    return currentTimeHHMM === scheduleTime;
}

// Make these functions available globally for other scripts
window.getServerAdjustedTime = getServerAdjustedTime;
window.checkScheduleTime = checkScheduleTime;