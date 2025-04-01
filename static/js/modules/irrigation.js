// Irrigation Module - Handles irrigation system functionality

// Timer variables
let runningTimer = null;
let runningTime = 0;

// Function to start the running timer
function startRunningTimer() {
    // Clear any existing timer
    stopRunningTimer();
    
    // Reset the running time
    runningTime = 0;
    
    // Update the display
    updateRunningTimeDisplay();
    
    // Start a new timer that updates every second
    runningTimer = setInterval(() => {
        runningTime++;
        updateRunningTimeDisplay();
    }, 1000);
}

// Function to stop the running timer
function stopRunningTimer() {
    if (runningTimer) {
        clearInterval(runningTimer);
        runningTimer = null;
    }
}

// Function to update the running time display
function updateRunningTimeDisplay() {
    const runningTimeElement = document.getElementById('running-time');
    if (runningTimeElement) {
        // Format the time as HH:MM:SS
        const hours = Math.floor(runningTime / 3600);
        const minutes = Math.floor((runningTime % 3600) / 60);
        const seconds = runningTime % 60;
        
        const formattedTime = [
            hours.toString().padStart(2, '0'),
            minutes.toString().padStart(2, '0'),
            seconds.toString().padStart(2, '0')
        ].join(':');
        
        runningTimeElement.textContent = formattedTime;
    }
}

// Export functions
window.startRunningTimer = startRunningTimer;
window.stopRunningTimer = stopRunningTimer;
window.updateRunningTimeDisplay = updateRunningTimeDisplay;