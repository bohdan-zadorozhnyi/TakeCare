/**
 * Chat List Functionality
 * Handles chat list sidebar interactions and new chat form
 */
document.addEventListener('DOMContentLoaded', function() {
    // New chat form visibility toggle
    const newChatButton = document.getElementById('newChatButton');
    const cancelChatButton = document.getElementById('cancelChat');
    const newChatForm = document.getElementById('newChatForm');

    if (newChatButton) {
        newChatButton.addEventListener('click', function() {
            newChatForm.style.display = 'block';
        });
    }

    if (cancelChatButton) {
        cancelChatButton.addEventListener('click', function() {
            newChatForm.style.display = 'none';
        });
    }

    // Toggle sidebar on mobile
    const toggleSidebarButton = document.getElementById('toggleSidebar');
    if (toggleSidebarButton) {
        toggleSidebarButton.addEventListener('click', function() {
            const sidebar = document.getElementById('chatSidebar');
            const mainChat = document.querySelector('.chat-main');
            sidebar.classList.toggle('mobile-show');
            mainChat.classList.toggle('mobile-hidden');
        });
    }

    // Handle mobile view when a chat is selected
    if (window.innerWidth < 768) {
        const chatItems = document.querySelectorAll('.chatroom-item');
        chatItems.forEach(item => {
            if (item.classList.contains('active')) {
                const sidebar = document.getElementById('chatSidebar');
                const mainChat = document.querySelector('.chat-main');
                sidebar.classList.remove('mobile-show');
                mainChat.classList.remove('mobile-hidden');
            }
        });
    }
});