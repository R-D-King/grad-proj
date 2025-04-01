// Clock Module - Handles server clock display

// Function to update the clock
function updateClock() {
    const clockElement = document.getElementById('server-clock');
    if (!clockElement) return;
    
    // Update the time locally every second
    const now = new Date();
    clockElement.textContent = now.toLocaleTimeString();
}

// Set up clock update interval
function setupClock() {
    // Update immediately
    updateClock();
    
    // Then update every second
    setInterval(updateClock, 1000);
    
    // Sync with server every minute to prevent drift
    setInterval(() => {
        fetch('/api/server-time/display')
            .then(response => response.json())
            .then(data => {
                const clockElement = document.getElementById('server-clock');
                if (clockElement) {
                    clockElement.textContent = data.time;
                }
            })
            .catch(error => {
                console.error('Error syncing clock with server:', error);
            });
    }, 60000);
}

// Export functions
window.updateClock = updateClock;
window.setupClock = setupClock;