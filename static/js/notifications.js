// WebSocket client for notifications
class NotificationClient {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // Starting delay in ms
        this.onNotification = null; // Callback to be set by consumer
        this.connected = false;
        this.queue = []; // Queue for messages when socket is not connected
    }

    connect() {
        if (!this.isSupported()) {
            console.warn('WebSockets are not supported by this browser');
            return;
        }

        // Determine the correct WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/ws/notifications/`;
        
        console.log('Connecting to notification WebSocket at:', wsUrl);
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = (event) => {
                console.log('Notification WebSocket connection established');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 2000; // Reset delay
                
                // Send any queued messages
                while (this.queue.length > 0) {
                    const message = this.queue.shift();
                    this.send(message);
                }
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Notification received:', data);
                    
                    if (this.onNotification) {
                        this.onNotification(data);
                    }
                    
                    // Show toast notification
                    this.showToast(data);
                } catch (e) {
                    console.error('Error processing notification:', e);
                }
            };
            
            this.socket.onclose = (event) => {
                console.log('Notification WebSocket connection closed');
                this.connected = false;
                
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    console.log(`Attempting to reconnect (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})...`);
                    setTimeout(() => this.connect(), this.reconnectDelay);
                    
                    // Exponential backoff
                    this.reconnectDelay *= 1.5;
                    this.reconnectAttempts++;
                } else {
                    console.warn('Maximum reconnection attempts reached');
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('Notification WebSocket error:', error);
            };
        } catch (e) {
            console.error('Error creating WebSocket connection:', e);
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.connected = false;
        }
    }
    
    send(message) {
        if (!this.connected) {
            this.queue.push(message);
            return;
        }
        
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            if (typeof message === 'object') {
                message = JSON.stringify(message);
            }
            this.socket.send(message);
        } else {
            this.queue.push(message);
        }
    }
    
    isSupported() {
        return 'WebSocket' in window;
    }
    
    markRead(notificationId) {
        this.send({
            action: 'mark_read',
            notification_id: notificationId
        });
    }
    
    markAllRead() {
        this.send({
            action: 'mark_all_read'
        });
    }
    
    showToast(notification) {
        // Create or get toast container
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Get notification type for styling
        const notificationType = notification.notification_type || notification.type || 'SYSTEM';
        
        // Create toast element
        const toastId = `toast-${Date.now()}`;
        const toast = document.createElement('div');
        toast.className = 'toast show';
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // Set toast content
        toast.innerHTML = `
            <div class="toast-header bg-${getBootstrapColor(notificationType)} bg-opacity-10">
                <strong class="me-auto">${getNotificationTypeLabel(notificationType)}</strong>
                <small>${new Date().toLocaleTimeString()}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${notification.message}
            </div>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            const bsToast = bootstrap.Toast.getOrCreateInstance(toast);
            bsToast.hide();
            
            // Remove from DOM after hiding
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        }, 5000);
        
        // Helper for mapping notification types to Bootstrap colors
        function getBootstrapColor(type) {
            const map = {
                'SYSTEM': 'secondary',
                'APPOINTMENT': 'success',
                'PRESCRIPTION': 'warning',
                'REFERRAL': 'info',
                'MEDICAL': 'danger'
            };
            return map[type] || 'primary';
        }
        
        function getNotificationTypeLabel(type) {
            const map = {
                'SYSTEM': 'System',
                'APPOINTMENT': 'Appointment',
                'PRESCRIPTION': 'Prescription',
                'REFERRAL': 'Referral',
                'MEDICAL': 'Medical'
            };
            return map[type] || 'Notification';
        }
    }
}

// Initialize notification client when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize for authenticated users
    if (document.body.classList.contains('logged-in')) {
        window.notificationClient = new NotificationClient();
        window.notificationClient.connect();
    }
});
