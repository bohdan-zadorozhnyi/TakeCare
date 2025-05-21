/**
 * TakeCare Notification System
 * Client-side JavaScript for WebSocket notifications
 */

class NotificationClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || window.location.host;
        this.token = options.token || this.getCSRFToken();
        this.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectInterval = options.reconnectInterval || 3000;
        this.onNotification = options.onNotification || this.defaultNotificationHandler;
        this.onConnect = options.onConnect || (() => console.log('Notification socket connected'));
        this.onDisconnect = options.onDisconnect || (() => console.log('Notification socket disconnected'));
        this.unreadCount = 0;
        
        // Bind methods to this
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.reconnect = this.reconnect.bind(this);
        this.handleMessage = this.handleMessage.bind(this);
        this.markAsRead = this.markAsRead.bind(this);
        this.markAllAsRead = this.markAllAsRead.bind(this);
    }
    
    /**
     * Connect to the notification WebSocket
     */
    connect() {
        if (this.socket) {
            this.disconnect();
        }
        
        try {
            // Connect to the notification WebSocket
            const wsUrl = `${this.protocol}//${this.baseUrl}/ws/notifications/`;
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('Notification WebSocket connection established');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.onConnect();
                
                // Fetch initial unread count
                this.getUnreadCount();
            };
            
            this.socket.onmessage = this.handleMessage;
            
            this.socket.onclose = (e) => {
                this.connected = false;
                console.log('Notification WebSocket connection closed:', e.code, e.reason);
                this.onDisconnect();
                
                // Try to reconnect if it wasn't a normal closure
                if (e.code !== 1000) {
                    this.reconnect();
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('Notification WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to connect to notification WebSocket:', error);
            this.reconnect();
        }
    }
    
    /**
     * Disconnect from the notification WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.connected = false;
        }
    }
    
    /**
     * Attempt to reconnect to the WebSocket
     */
    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnect attempts reached. Giving up.');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectInterval);
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // Handle notification messages
            if (data.notification_id) {
                this.unreadCount++;
                this.updateUnreadCountBadge();
                this.onNotification(data);
            }
            
            // Handle status responses
            if (data.status) {
                if (data.action === 'mark_read' && data.notification_id) {
                    this.unreadCount = Math.max(0, this.unreadCount - 1);
                    this.updateUnreadCountBadge();
                } else if (data.action === 'mark_all_read') {
                    this.unreadCount = 0;
                    this.updateUnreadCountBadge();
                }
            }
        } catch (error) {
            console.error('Error parsing notification message:', error);
        }
    }
    
    /**
     * Default handler for notifications
     */
    defaultNotificationHandler(data) {
        console.log('Notification received:', data);
        
        // If browser notifications are supported and permitted
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification('TakeCare Notification', {
                body: data.message,
                icon: '/static/images/logo.png'
            });
        }
        
        // You can implement your own UI notification here
    }
    
    /**
     * Mark a notification as read
     */
    markAsRead(notificationId) {
        if (!this.connected || !this.socket) {
            console.warn('Cannot mark notification as read: WebSocket not connected');
            return;
        }
        
        this.socket.send(JSON.stringify({
            action: 'mark_read',
            notification_id: notificationId
        }));
    }
    
    /**
     * Mark all notifications as read
     */
    markAllAsRead() {
        if (!this.connected || !this.socket) {
            console.warn('Cannot mark all notifications as read: WebSocket not connected');
            return;
        }
        
        this.socket.send(JSON.stringify({
            action: 'mark_all_read'
        }));
    }
    
    /**
     * Get the unread notification count from the API
     */
    getUnreadCount() {
        fetch('/api/v1/notifications/unread-count/')
            .then(response => response.json())
            .then(data => {
                this.unreadCount = data.unread_count;
                this.updateUnreadCountBadge();
            })
            .catch(error => {
                console.error('Error fetching unread count:', error);
            });
    }
    
    /**
     * Update the unread count badge in the UI
     */
    updateUnreadCountBadge() {
        // Find notification count badge elements
        const badges = document.querySelectorAll('.notification-badge');
        
        badges.forEach(badge => {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        });
        
        // Dispatch event for other parts of the app
        window.dispatchEvent(new CustomEvent('notifications-updated', {
            detail: { count: this.unreadCount }
        }));
    }
    
    /**
     * Request permission for browser notifications
     */
    requestNotificationPermission() {
        if ("Notification" in window) {
            if (Notification.permission !== "granted" && Notification.permission !== "denied") {
                Notification.requestPermission();
            }
        }
    }
    
    /**
     * Get CSRF token from cookies
     */
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith('csrftoken=')) {
                return cookie.substring('csrftoken='.length);
            }
        }
        return '';
    }
}

// Initialize notification client when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if the user is logged in
    if (document.body.classList.contains('logged-in')) {
        window.notificationClient = new NotificationClient({
            onNotification: (data) => {
                // Show a toast notification
                const toast = document.createElement('div');
                toast.className = 'notification-toast';
                toast.innerHTML = `
                    <div class="notification-toast-content">
                        <h4>${data.type || 'Notification'}</h4>
                        <p>${data.message}</p>
                    </div>
                    <button class="notification-toast-close">×</button>
                `;
                
                document.body.appendChild(toast);
                
                // Add animation
                setTimeout(() => {
                    toast.classList.add('show');
                }, 10);
                
                // Auto-dismiss after 5 seconds
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => {
                        toast.remove();
                    }, 300);
                }, 5000);
                
                // Close button
                const closeBtn = toast.querySelector('.notification-toast-close');
                closeBtn.addEventListener('click', () => {
                    toast.classList.remove('show');
                    setTimeout(() => {
                        toast.remove();
                    }, 300);
                });
                
                // Mark as read when clicked
                toast.addEventListener('click', () => {
                    window.notificationClient.markAsRead(data.notification_id);
                    // Redirect to related page if applicable
                    if (data.related_url) {
                        window.location.href = data.related_url;
                    }
                });
            }
        });
        
        window.notificationClient.connect();
        window.notificationClient.requestNotificationPermission();
    }
});
