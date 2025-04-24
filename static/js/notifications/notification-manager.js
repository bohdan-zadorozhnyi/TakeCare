/**
 * Notification Manager
 * Handles WebSocket connections for real-time notifications
 */
class NotificationManager {
    constructor(options = {}) {
        this.options = {
            autoConnect: true,
            notificationBadgeSelector: '#notification-badge',
            notificationMenuSelector: '#notification-dropdown',
            notificationListSelector: '#notification-list',
            maxNotifications: 5,
            ...options
        };
        
        this.socket = null;
        this.connected = false;
        this.unreadCount = 0;
        this.notificationBadge = document.querySelector(this.options.notificationBadgeSelector);
        this.notificationMenu = document.querySelector(this.options.notificationMenuSelector);
        this.notificationList = document.querySelector(this.options.notificationListSelector);
        
        if (this.options.autoConnect) {
            this.connect();
        }
    }
    
    /**
     * Connect to the WebSocket server
     */
    connect() {
        // Create WebSocket connection
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/notifications/`;
        
        this.socket = new WebSocket(wsUrl);
        
        // Connection opened
        this.socket.addEventListener('open', (event) => {
            this.connected = true;
            console.log('Connected to notification server');
        });
        
        // Listen for messages
        this.socket.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        });
        
        // Connection closed
        this.socket.addEventListener('error', (event) => {
            console.error('WebSocket error:', event);
            this.reconnect();
        });
        
        // Connection closed
        this.socket.addEventListener('close', (event) => {
            this.connected = false;
            console.log('Connection to notification server closed');
            this.reconnect();
        });
    }
    
    /**
     * Attempt to reconnect
     */
    reconnect() {
        if (!this.connected) {
            // Wait a bit before reconnecting
            setTimeout(() => {
                console.log('Attempting to reconnect to notification server...');
                this.connect();
            }, 5000); // 5 second delay
        }
    }
    
    /**
     * Close the WebSocket connection
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(data) {
        switch (data.action) {
            case 'initial_status':
                this.unreadCount = data.unread_count;
                this.updateNotificationBadge();
                this.updateNotificationList(data.recent_notifications);
                break;
            case 'new_notification':
                this.handleNewNotification(data.notification);
                break;
            case 'unread_count_update':
                this.unreadCount = data.count;
                this.updateNotificationBadge();
                break;
            case 'mark_read_response':
            case 'mark_all_read_response':
                // Update UI if necessary
                break;
            default:
                console.log('Unknown action:', data.action);
        }
    }
    
    /**
     * Handle a new notification
     */
    handleNewNotification(notification) {
        // Increment unread count
        this.unreadCount++;
        this.updateNotificationBadge();
        
        // Add to notification list
        if (this.notificationList) {
            this.addNotificationToList(notification);
        }
        
        // Display notification
        this.showNotificationAlert(notification);
    }
    
    /**
     * Update the notification badge counter
     */
    updateNotificationBadge() {
        if (this.notificationBadge) {
            if (this.unreadCount > 0) {
                this.notificationBadge.textContent = this.unreadCount;
                this.notificationBadge.classList.remove('d-none');
            } else {
                this.notificationBadge.classList.add('d-none');
            }
        }
    }
    
    /**
     * Update the notification dropdown menu
     */
    updateNotificationList(notifications) {
        if (!this.notificationList) return;
        
        // Clear existing items
        this.notificationList.innerHTML = '';
        
        // Add new items
        if (notifications.length > 0) {
            notifications.slice(0, this.options.maxNotifications).forEach(notification => {
                this.addNotificationToList(notification);
            });
            
            // Add "See all" link if there are more
            if (notifications.length > 0) {
                const seeAllItem = document.createElement('li');
                seeAllItem.className = 'dropdown-item text-center border-top pt-2 mt-2';
                seeAllItem.innerHTML = `<a href="/notifications/" class="text-primary">See all notifications</a>`;
                this.notificationList.appendChild(seeAllItem);
            }
        } else {
            // No notifications
            const emptyItem = document.createElement('li');
            emptyItem.className = 'dropdown-item text-center';
            emptyItem.textContent = 'No notifications';
            this.notificationList.appendChild(emptyItem);
        }
    }
    
    /**
     * Add a notification to the dropdown list
     */
    addNotificationToList(notification) {
        if (!this.notificationList) return;
        
        // Check if it's at capacity
        if (this.notificationList.querySelectorAll('.notification-item:not(.see-all)').length >= this.options.maxNotifications) {
            // Remove the oldest notification
            const oldest = this.notificationList.querySelector('.notification-item:last-child:not(.see-all)');
            if (oldest) {
                oldest.remove();
            }
        }
        
        // Create notification element
        const item = document.createElement('li');
        item.className = `dropdown-item notification-item ${notification.read ? '' : 'unread'}`;
        
        // Get appropriate icon based on notification type
        let icon = 'bell';
        switch (notification.type) {
            case 'APPOINTMENT':
                icon = 'calendar-alt';
                break;
            case 'PRESCRIPTION':
                icon = 'prescription-bottle-alt';
                break;
            case 'REFERRAL':
                icon = 'file-medical';
                break;
            case 'ISSUE':
                icon = 'exclamation-triangle';
                break;
            case 'ADMIN':
                icon = 'bullhorn';
                break;
        }
        
        // Format date
        const date = new Date(notification.date);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Set content
        item.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="notification-icon me-2">
                    <i class="fas fa-${icon}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-text">${notification.message}</div>
                    <div class="notification-time small text-muted">${formattedDate}</div>
                </div>
            </div>
        `;
        
        // Add click handler
        item.addEventListener('click', () => {
            window.location.href = `/notifications/${notification.id}/`;
        });
        
        // Insert at the beginning
        this.notificationList.prepend(item);
    }
    
    /**
     * Show a browser notification alert
     */
    showNotificationAlert(notification) {
        // Check if browser notifications are supported
        if (!("Notification" in window)) {
            return;
        }
        
        // Check if permission is granted
        if (Notification.permission === "granted") {
            this.createBrowserNotification(notification);
        }
        // Otherwise, request permission and show notification if granted
        else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    this.createBrowserNotification(notification);
                }
            });
        }
    }
    
    /**
     * Create a browser notification
     */
    createBrowserNotification(notification) {
        // Get appropriate icon based on notification type
        let icon = '/static/img/logo.png'; // Default icon
        let title = 'New Notification';
        
        switch (notification.type) {
            case 'APPOINTMENT':
                title = 'Appointment Notification';
                break;
            case 'PRESCRIPTION':
                title = 'Prescription Notification';
                break;
            case 'REFERRAL':
                title = 'Referral Notification';
                break;
            case 'ISSUE':
                title = 'Issue Alert';
                break;
            case 'ADMIN':
                title = 'Admin Announcement';
                break;
        }
        
        // Create and show the notification
        const browserNotification = new Notification(title, {
            body: notification.message,
            icon: icon
        });
        
        // Handle notification click
        browserNotification.addEventListener('click', () => {
            window.focus();
            window.location.href = `/notifications/${notification.id}/`;
        });
        
        // Auto-close after 5 seconds
        setTimeout(() => {
            browserNotification.close();
        }, 5000);
    }
    
    /**
     * Mark a notification as read
     */
    markAsRead(notificationId) {
        if (!this.connected || !this.socket) return;
        
        this.socket.send(JSON.stringify({
            action: 'mark_read',
            id: notificationId
        }));
    }
    
    /**
     * Mark all notifications as read
     */
    markAllAsRead() {
        if (!this.connected || !this.socket) return;
        
        this.socket.send(JSON.stringify({
            action: 'mark_all_read'
        }));
    }
}

// Initialize notification manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated (by checking for the notification badge element)
    const notificationBadge = document.getElementById('notification-badge');
    
    if (notificationBadge) {
        // Initialize notification manager
        window.notificationManager = new NotificationManager();
    }
});