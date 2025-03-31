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
            
            // Update any time displays
            updateTimeDisplays();
        })
        .catch(error => {
            console.error('Error syncing time with server:', error);
        });
}

// Get current time adjusted to server time
function getServerAdjustedTime() {
    return new Date(Date.now() + serverTimeOffset);
}

// Format time as HH:MM
function formatTimeHHMM(date) {
    return date.getHours().toString().padStart(2, '0') + ':' + 
           date.getMinutes().toString().padStart(2, '0');
}

// Update any time displays on the page
function updateTimeDisplays() {
    const serverTime = getServerAdjustedTime();
    
    // Update server time display if it exists
    const timeDisplay = document.getElementById('server-time-display');
    if (timeDisplay) {
        timeDisplay.textContent = serverTime.toLocaleTimeString();
    }
}

// Sync time when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initial sync
    syncServerTime();
    
    // Set up periodic sync (every 15 minutes)
    setInterval(syncServerTime, 15 * 60 * 1000);
    
    // Update clock display every second
    setInterval(updateTimeDisplays, 1000);
});

// Function to check if a schedule should run based on server time
function checkScheduleTime(scheduleTime) {
    const serverTime = getServerAdjustedTime();
    const currentTimeHHMM = formatTimeHHMM(serverTime);
    return currentTimeHHMM === scheduleTime;
}