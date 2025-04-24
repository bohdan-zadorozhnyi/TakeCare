/**
 * Calendar functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the calendar element
    const calendarEl = document.getElementById('calendar');
    
    // Get the view selector
    const viewSelector = document.getElementById('view-selector');
    
    // Initialize the calendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: viewSelector.value,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: ''
        },
        events: appointmentsJsonUrl, // This will be defined in the template
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            meridiem: 'short'
        },
        height: '100%',
        expandRows: true,
        slotMinTime: '08:00:00',
        slotMaxTime: '20:00:00',
        allDaySlot: false,
        nowIndicator: true,
        navLinks: true,
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5],  // Monday - Friday
            startTime: '08:00',
            endTime: '18:00',
        },
        eventClick: function(info) {
            window.location.href = info.event.url;
        },
        loading: function(isLoading) {
            if (isLoading) {
                // Show loading indicator
                console.log('Loading events...');
            } else {
                // Hide loading indicator
                console.log('Events loaded.');
            }
        }
    });
    
    // Initialize the calendar
    calendar.render();
    
    // Handle view change
    viewSelector.addEventListener('change', function() {
        calendar.changeView(this.value);
    });
    
    // Settings modal handling
    const settingsModal = document.getElementById('settings-modal');
    const settingsBtn = document.getElementById('settings-btn');
    const closeSettings = document.getElementById('close-settings');
    
    settingsBtn.addEventListener('click', function() {
        settingsModal.classList.add('active');
    });
    
    closeSettings.addEventListener('click', function() {
        settingsModal.classList.remove('active');
    });
    
    // Close modal when clicking outside
    settingsModal.addEventListener('click', function(e) {
        if (e.target === this) {
            settingsModal.classList.remove('active');
        }
    });
    
    // Handle add slot button for doctors if it exists
    const addSlotBtn = document.getElementById('add-slot-btn');
    if (addSlotBtn) {
        addSlotBtn.addEventListener('click', function() {
            // For now, just show an alert that this feature is coming soon
            alert('Create appointment slot feature is coming soon!');
        });
    }
});