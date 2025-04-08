// Schedules Module - Handles schedule management

// Function to save a new schedule
async function saveNewSchedule() {
    const presetId = getSelectedPresetId();
    if (!presetId) {
        alert('Please select a preset first');
        return;
    }

    const startTime = document.getElementById('scheduleStartTime').value;
    const duration = document.getElementById('scheduleDuration').value;

    if (!startTime || !duration) {
        alert('Please fill in all fields');
        return;
    }

    try {
        const response = await fetch(`/api/irrigation/schedule`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                preset_id: presetId,
                start_time: startTime,
                duration: parseInt(duration)
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Schedule created:', result);

        // Close the modal
        addScheduleModal.hide();

        // Reset the form
        document.getElementById('addScheduleForm').reset();

        // Refresh the preset details to show the new schedule
        showPresetDetails(presetId);

    } catch (error) {
        console.error('Error saving schedule:', error);
        alert('Failed to save schedule. Please try again.');
    }
}

// Function to update an existing schedule
async function updateSchedule() {
    const scheduleId = document.getElementById('editScheduleId').value;
    const startTime = document.getElementById('editScheduleTime').value;
    const duration = document.getElementById('editScheduleDuration').value;
    const active = document.getElementById('editScheduleActive').checked;

    try {
        const response = await fetch(`/api/irrigation/schedule/${scheduleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_time: startTime,
                duration: parseInt(duration),
                active: active
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Schedule updated:', result);

        // Close the modal
        editScheduleModal.hide();

        // Refresh the preset details
        const presetId = getSelectedPresetId();
        if (presetId) {
            showPresetDetails(presetId);
        }

    } catch (error) {
        console.error('Error updating schedule:', error);
        alert('Failed to update schedule. Please try again.');
    }
}

// Function to delete a schedule
async function deleteSchedule(scheduleId) {
    if (!confirm('Are you sure you want to delete this schedule?')) {
        return;
    }

    try {
        const response = await fetch(`/api/irrigation/schedule/${scheduleId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Refresh the preset details
        const presetId = getSelectedPresetId();
        if (presetId) {
            showPresetDetails(presetId);
        }

    } catch (error) {
        console.error('Error deleting schedule:', error);
        alert('Failed to delete schedule. Please try again.');
    }
}

// Export the functions
window.saveNewSchedule = saveNewSchedule;
window.updateSchedule = updateSchedule;
window.deleteSchedule = deleteSchedule;