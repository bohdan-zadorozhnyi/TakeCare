// Enhanced notification testing functionality
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're in development mode and add testing functions
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || true) {
        // Create test button container
        const testContainer = document.createElement('div');
        testContainer.className = 'position-fixed bottom-0 end-0 p-3';
        testContainer.style.zIndex = '1050';
        testContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        testContainer.style.borderRadius = '5px';
        testContainer.style.border = '1px solid #ddd';
        testContainer.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
        testContainer.style.padding = '10px';
        
        // Create dropdown for notification type
        const typeSelector = document.createElement('select');
        typeSelector.className = 'form-select form-select-sm mb-2';
        typeSelector.id = 'notification-type-select';
        
        // Add options
        const types = [
            { value: 'SYSTEM', label: 'System' },
            { value: 'APPOINTMENT', label: 'Appointment' },
            { value: 'PRESCRIPTION', label: 'Prescription' },
            { value: 'REFERRAL', label: 'Referral' },
            { value: 'MEDICAL', label: 'Medical' }
        ];
        
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.value;
            option.textContent = type.label;
            typeSelector.appendChild(option);
        });
        
        // Create test buttons
        const testButton = document.createElement('button');
        testButton.className = 'btn btn-sm btn-primary w-100';
        testButton.innerHTML = '<i class="fas fa-bell"></i> Send Test Notification';
        testButton.onclick = function() {
            const type = document.getElementById('notification-type-select').value;
            sendTestNotification(type);
        };
        
        // Add elements to container
        testContainer.appendChild(document.createTextNode('Test Notifications'));
        testContainer.appendChild(document.createElement('hr'));
        testContainer.appendChild(typeSelector);
        testContainer.appendChild(testButton);
        
        // Add to page
        document.body.appendChild(testContainer);
    }
    
    // Function to send a test notification
    function sendTestNotification(type = 'SYSTEM') {
        fetch('/api/v1/notifications/test/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                message: `This is a test ${type.toLowerCase()} notification sent at ${new Date().toLocaleTimeString()}`,
                notification_type: type
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Test notification sent:', data);
        })
        .catch(error => {
            console.error('Error sending test notification:', error);
            alert('Could not send test notification. See console for details.');
        });
    }
    
    // Get CSRF token
    function getCsrfToken() {
        const csrfCookie = document.cookie
            .split(';')
            .map(cookie => cookie.trim())
            .find(cookie => cookie.startsWith('csrftoken='));
            
        if (csrfCookie) {
            return csrfCookie.split('=')[1];
        }
        
        // Fallback to getting from a form
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
});
