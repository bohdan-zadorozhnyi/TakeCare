// Test notification functionality
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're in development mode and add testing functions
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        // Create test button container
        const testContainer = document.createElement('div');
        testContainer.className = 'position-fixed bottom-0 end-0 p-3';
        testContainer.style.zIndex = '1050';
        
        // Create test button
        const testButton = document.createElement('button');
        testButton.className = 'btn btn-sm btn-secondary';
        testButton.innerHTML = '<i class="fas fa-bell"></i> Test Notification';
        testButton.onclick = sendTestNotification;
        
        // Add to page
        testContainer.appendChild(testButton);
        document.body.appendChild(testContainer);
    }
    
    // Function to send a test notification
    function sendTestNotification() {
        fetch('/api/v1/notifications/test/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                message: 'This is a test notification sent at ' + new Date().toLocaleTimeString()
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
