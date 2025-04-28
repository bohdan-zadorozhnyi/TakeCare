/**
 * Chat Detail Functionality
 * Handles WebSocket connections, message sending/receiving, and UI interactions
 */
class ChatDetailManager {
    constructor(chatRoomId, currentUserId) {
        this.chatRoomId = chatRoomId;
        this.currentUserId = currentUserId;
        this.messageForm = document.getElementById('message-form');
        this.messagesContainer = document.getElementById('messages');
        this.errorMessage = document.getElementById('error-message');
        this.messageInput = document.getElementById('message-content');
        
        this.initializeChat();
    }

    /**
     * Set up event listeners and WebSocket connection
     */
    initializeChat() {
        // Add mobile class for responsiveness
        if (window.innerWidth < 768) {
            document.body.classList.add('mobile-chat-view');
            
            // Initially hide the sidebar on mobile when a chat is open
            const sidebar = document.getElementById('chatSidebar');
            if (sidebar) {
                sidebar.classList.remove('mobile-show');
            }
        }

        // Auto resize textarea as user types
        if (this.messageInput) {
            this.messageInput.addEventListener('input', () => this.resizeMessageInput());
        }

        // Set up WebSocket connection
        this.setupWebSocket();

        // Set up message form submission
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => this.handleMessageSubmit(e));
        }

        // Scroll to bottom on page load
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }

        // Highlight active chat
        this.highlightActiveChat();
    }

    /**
     * Set up WebSocket connection for real-time messaging
     */
    setupWebSocket() {
        // WebSocket connection
        this.chatSocket = new WebSocket(
            'ws://' + window.location.host + '/ws/chat/' + this.chatRoomId + '/'
        );

        this.chatSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.displayNewMessage(data);
        };

        this.chatSocket.onclose = (e) => {
            this.showError(
                'Chat connection closed. Please refresh the page.',
                'connection_error'
            );
        };
    }

    /**
     * Display a new message in the chat
     */
    displayNewMessage(data) {
        const messageElement = document.createElement('div');
        const isSender = data.sender_id === this.currentUserId;
        messageElement.className = `message ${isSender ? 'sent' : 'received'}`;
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${data.message}</p>
                <span class="timestamp">${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
        `;
        this.messagesContainer.appendChild(messageElement);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    /**
     * Handle message form submission
     */
    handleMessageSubmit(e) {
        e.preventDefault();
        const message = this.messageInput.value.trim();

        if (!message) {
            this.showError('Message content cannot be empty', 'empty_content');
            return;
        }

        // Send message using WebSocket
        this.chatSocket.send(JSON.stringify({
            'message': message
        }));

        this.messageInput.value = '';
        this.messageInput.style.height = '40px'; // Reset height after sending
        this.messageInput.focus(); // Keep focus on input after sending
    }

    /**
     * Auto resize the textarea as user types
     */
    resizeMessageInput() {
        this.messageInput.style.height = 'auto';
        const newHeight = Math.min(this.messageInput.scrollHeight, 120); // Max height of 120px
        this.messageInput.style.height = newHeight + 'px';
    }

    /**
     * Show error messages in the UI
     */
    showError(error, type, details = null) {
        const errorDiv = document.getElementById('error-message');
        const titles = {
            'connection_error': 'Connection Error',
            'message_error': 'Message Error',
            'empty_content': 'Invalid Message'
        };

        errorDiv.querySelector('.error-title').textContent = titles[type] || 'Error';
        errorDiv.querySelector('.error-content').textContent = error;

        if (details) {
            errorDiv.querySelector('.error-details').textContent = details;
            errorDiv.querySelector('.error-details').style.display = 'block';
        } else {
            errorDiv.querySelector('.error-details').style.display = 'none';
        }

        errorDiv.classList.add('show');
        setTimeout(() => {
            errorDiv.classList.remove('show');
        }, 5000);
    }

    /**
     * Highlight the active chat in the sidebar
     */
    highlightActiveChat() {
        const chatItems = document.querySelectorAll('.chatroom-item');
        chatItems.forEach(item => {
            if (item.querySelector('a').href.includes(this.chatRoomId)) {
                item.classList.add('active');
            }
        });
    }
}

// Initialize chat manager when data is available
function initializeChatDetail(chatRoomId, currentUserId) {
    new ChatDetailManager(chatRoomId, currentUserId);
}