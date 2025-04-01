// Reports Module - Handles report generation and display

// Function to toggle report options based on report type
function toggleReportOptions() {
    const reportType = document.getElementById('report-type').value;
    console.log(`Report type changed to: ${reportType}`);
    
    // Get option containers
    const weatherOptions = document.getElementById('weather-options');
    const irrigationOptions = document.getElementById('irrigation-options');
    
    if (!weatherOptions || !irrigationOptions) {
        console.error('Report option containers not found');
        return;
    }
    
    // Show/hide based on report type
    if (reportType === 'weather') {
        weatherOptions.style.display = 'block';
        irrigationOptions.style.display = 'none';
    } else {
        weatherOptions.style.display = 'none';
        irrigationOptions.style.display = 'block';
    }
    
    console.log(`Toggled options for ${reportType} report`);
}

// Function to set default dates if they're empty
function setDefaultDates() {
    let startDate = document.getElementById('report-start-date').value;
    let endDate = document.getElementById('report-end-date').value;
    
    // If dates are empty, set them to default values and update the input fields
    if (!startDate || !endDate) {
        const today = new Date();
        const lastWeek = new Date(today);
        lastWeek.setDate(today.getDate() - 7);
        
        const formatDate = (date) => {
            return date.toISOString().split('T')[0];
        };
        
        if (!startDate) {
            startDate = formatDate(lastWeek);
            document.getElementById('report-start-date').value = startDate;
        }
        if (!endDate) {
            endDate = formatDate(today);
            document.getElementById('report-end-date').value = endDate;
        }
    }
    
    return { startDate, endDate };
}

// Function to generate a report
function generateReport() {
    const reportType = document.getElementById('report-type').value;
    
    // Set default dates if empty
    const { startDate, endDate } = setDefaultDates();
    
    // Get selected options
    const options = {};
    if (reportType === 'weather') {
        options.temperature = document.getElementById('weather-temperature').checked;
        options.humidity = document.getElementById('weather-humidity').checked;
        options.soil_moisture = document.getElementById('weather-soil-moisture').checked;
        options.wind_speed = document.getElementById('weather-wind-speed').checked;
        options.pressure = document.getElementById('weather-pressure').checked;
    } else {
        options.pump_status = document.getElementById('irrigation-pump-status').checked;
        options.water_level = document.getElementById('irrigation-water-level').checked;
        options.duration = document.getElementById('irrigation-duration').checked;
    }
    
    fetch('/api/reports/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            report_type: reportType,
            start_date: startDate,
            end_date: endDate,
            options: options
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Report data:', data);
        displayReport(data, reportType);
    })
    .catch(error => {
        console.error('Error generating report:', error);
        showAlert('Error generating report. Please try again.', 'danger');
    });
}

// Function to display a report
function displayReport(data, reportType) {
    const reportDisplay = document.getElementById('report-display');
    if (!reportDisplay) {
        console.error('Report display container not found');
        return;
    }
    
    if (!data || data.length === 0) {
        reportDisplay.innerHTML = '<div class="alert alert-info">No data available for the selected period.</div>';
        return;
    }
    
    // Create table headers based on report type
    let headers = ['Date', 'Time'];
    if (reportType === 'weather') {
        // Add weather-specific headers
        if (data[0].temperature !== undefined) headers.push('Temperature (°C)');
        if (data[0].humidity !== undefined) headers.push('Humidity (%)');
        if (data[0].soil_moisture !== undefined) headers.push('Soil Moisture (%)');
        if (data[0].wind_speed !== undefined) headers.push('Wind Speed (km/h)');
        if (data[0].pressure !== undefined) headers.push('Pressure (hPa)');
    } else {
        // Add irrigation-specific headers
        if (data[0].pump_status !== undefined) headers.push('Pump Status');
        if (data[0].water_level !== undefined) headers.push('Water Level (%)');
        if (data[0].duration !== undefined) headers.push('Duration (s)');
    }
    
    // Create table HTML
    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        ${headers.map(header => `<th>${header}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add rows for each data point
    data.forEach(item => {
        const timestamp = new Date(item.timestamp);
        const date = timestamp.toLocaleDateString();
        const time = timestamp.toLocaleTimeString();
        
        tableHTML += '<tr>';
        tableHTML += `<td>${date}</td>`;
        tableHTML += `<td>${time}</td>`;
        
        if (reportType === 'weather') {
            // Add weather-specific data
            if (headers.includes('Temperature (°C)')) tableHTML += `<td>${item.temperature !== undefined ? item.temperature : '-'}</td>`;
            if (headers.includes('Humidity (%)')) tableHTML += `<td>${item.humidity !== undefined ? item.humidity : '-'}</td>`;
            if (headers.includes('Soil Moisture (%)')) tableHTML += `<td>${item.soil_moisture !== undefined ? item.soil_moisture : '-'}</td>`;
            if (headers.includes('Wind Speed (km/h)')) tableHTML += `<td>${item.wind_speed !== undefined ? item.wind_speed : '-'}</td>`;
            if (headers.includes('Pressure (hPa)')) tableHTML += `<td>${item.pressure !== undefined ? item.pressure : '-'}</td>`;
        } else {
            // Add irrigation-specific data
            if (headers.includes('Pump Status')) tableHTML += `<td>${item.pump_status !== undefined ? (item.pump_status ? 'Running' : 'Stopped') : '-'}</td>`;
            if (headers.includes('Water Level (%)')) tableHTML += `<td>${item.water_level !== undefined ? item.water_level : '-'}</td>`;
            if (headers.includes('Duration (s)')) tableHTML += `<td>${item.duration !== undefined ? item.duration : '-'}</td>`;
        }
        
        tableHTML += '</tr>';
    });
    
    tableHTML += `
                </tbody>
            </table>
        </div>
    `;
    
    reportDisplay.innerHTML = tableHTML;
}

// Function to download a report
function downloadReport() {
    const reportType = document.getElementById('report-type').value;
    
    // Set default dates if empty
    const { startDate, endDate } = setDefaultDates();
    
    // Get selected options
    const options = {};
    if (reportType === 'weather') {
        options.temperature = document.getElementById('weather-temperature').checked;
        options.humidity = document.getElementById('weather-humidity').checked;
        options.soil_moisture = document.getElementById('weather-soil-moisture').checked;
        options.wind_speed = document.getElementById('weather-wind-speed').checked;
        options.pressure = document.getElementById('weather-pressure').checked;
    } else {
        options.pump_status = document.getElementById('irrigation-pump-status').checked;
        options.water_level = document.getElementById('irrigation-water-level').checked;
        options.duration = document.getElementById('irrigation-duration').checked;
    }
    
    // Create URL with parameters
    const url = `/api/reports/download?report_type=${reportType}&start_date=${startDate}&end_date=${endDate}&options=${JSON.stringify(options)}`;
    
    // First check if data is available
    fetch(url)
        .then(response => {
            // Check if the response is JSON (our no-data message) or a file
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                // This is our JSON response, likely the no-data message
                return response.json().then(data => {
                    if (data.status === 'no_data') {
                        // Show popup with the message
                        showAlert(data.message, 'warning');
                        return null;
                    }
                    return data;
                });
            } else {
                // This is a file download, trigger it
                response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    // Include dates in the filename
                    a.download = `${reportType}_report_${startDate}_to_${endDate}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    showAlert('Report downloaded successfully', 'success');
                });
                return null;
            }
        })
        .catch(error => {
            console.error('Error downloading report:', error);
            showAlert('Error downloading report. Please try again.', 'danger');
        });
}

// Function to clear the report display
function clearReports() {
    const reportDisplay = document.getElementById('report-display');
    if (reportDisplay) {
        reportDisplay.innerHTML = '';
        console.log('Reports cleared');
        showAlert('Report display cleared', 'info');
    }
}

// Export functions
window.toggleReportOptions = toggleReportOptions;
window.generateReport = generateReport;
window.downloadReport = downloadReport;
window.clearReports = clearReports;