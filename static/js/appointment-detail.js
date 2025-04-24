/**
 * Appointment Detail functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Calculate end time
    function calculateEndTime(startTime, duration) {
        // Parse start time
        const [timePart, period] = startTime.split(' ');
        const [hours, minutes] = timePart.split(':').map(num => parseInt(num, 10));
        
        // Convert to 24-hour format
        let totalMinutes = hours * 60 + parseInt(minutes);
        if (period === 'PM' && hours < 12) {
            totalMinutes += 12 * 60;
        } else if (period === 'AM' && hours === 12) {
            totalMinutes = parseInt(minutes);
        }
        
        // Add duration
        totalMinutes += duration;
        
        // Convert back to 12-hour format
        let endHours = Math.floor(totalMinutes / 60);
        const endMinutes = totalMinutes % 60;
        let endPeriod = 'AM';
        
        if (endHours >= 12) {
            endPeriod = 'PM';
            if (endHours > 12) {
                endHours -= 12;
            }
        }
        
        if (endHours === 0) {
            endHours = 12;
        }
        
        // Format the end time
        return `${endHours}:${endMinutes.toString().padStart(2, '0')} ${endPeriod}`;
    }

    // Apply end time calculation if the necessary elements are present
    const endTimeEl = document.getElementById('end-time');
    if (endTimeEl && typeof startTimeStr !== 'undefined' && typeof appointmentDuration !== 'undefined') {
        const endTime = calculateEndTime(startTimeStr, appointmentDuration);
        endTimeEl.textContent = endTime;
    }
});