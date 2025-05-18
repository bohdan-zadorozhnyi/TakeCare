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
        dateClick: function(info) {
            // When a date is clicked, pre-fill the date in the add slot form
            const addSlotBtn = document.getElementById('add-slot-btn');
            if (addSlotBtn) {
                // Pre-fill the date in the form
                document.getElementById('slot_date').value = info.dateStr.split('T')[0];
                
                // If there's a time component, pre-fill that too
                if (info.dateStr.includes('T')) {
                    const timeStr = info.dateStr.split('T')[1].substring(0, 5); // Get HH:MM format
                    document.getElementById('slot_time').value = timeStr;
                }
                
                // Show the modal
                document.getElementById('add-slot-modal').classList.add('active');
            }
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
    
    // Handle add slot button for doctors
    const addSlotBtn = document.getElementById('add-slot-btn');
    const addSlotModal = document.getElementById('add-slot-modal');
    const closeAddSlot = document.getElementById('close-add-slot');
    
    // if (addSlotBtn) {
    //     // Set today's date as the default in the date field
    //     const today = new Date();
    //     const dateStr = today.toISOString().split('T')[0];
    //     document.getElementById('slot_date').value = dateStr;
        
    //     // Set a default time
    //     document.getElementById('slot_time').value = "09:00";
        
    //     // Show modal when button is clicked
    //     addSlotBtn.addEventListener('click', function() {
    //         addSlotModal.classList.add('active');
    //     });
        
    //     // Close modal with close button
    //     closeAddSlot.addEventListener('click', function() {
    //         addSlotModal.classList.remove('active');
    //     });
        
    //     // Close modal when clicking outside
    //     addSlotModal.addEventListener('click', function(e) {
    //         if (e.target === this) {
    //             addSlotModal.classList.remove('active');
    //         }
    //     });
        
    //     // Toggle recurring options visibility
    //     const isRecurringCheckbox = document.getElementById('is_recurring');
    //     const recurringOptions = document.getElementById('recurring-options');
        
    //     isRecurringCheckbox.addEventListener('change', function() {
    //         if (this.checked) {
    //             recurringOptions.style.display = 'block';
    //         } else {
    //             recurringOptions.style.display = 'none';
    //         }
    //     });
        
    //     // Handle form submission via AJAX
    //     const addSlotForm = document.getElementById('add-slot-form');
    //     addSlotForm.addEventListener('submit', function(e) {
    //         e.preventDefault();
            
    //         const formData = new FormData(this);
            
    //         fetch(this.action, {
    //             method: 'POST',
    //             body: formData,
    //             headers: {
    //                 'X-Requested-With': 'XMLHttpRequest',
    //             }
    //         })
    //         .then(response => response.json())
    //         .then(data => {
    //             if (data.status === 'success') {
    //                 // Close the modal
    //                 addSlotModal.classList.remove('active');
                    
    //                 // Refresh the calendar to show the new slots
    //                 calendar.refetchEvents();
                    
    //                 // Show success message
    //                 alert(data.message);
    //             } else {
    //                 // Show error message
    //                 alert('Error: ' + data.message);
    //             }
    //         })
    //         .catch(error => {
    //             console.error('Error:', error);
    //             alert('An error occurred while creating the appointment slot. Please try again.');
    //         });
    //     });
    // }
});