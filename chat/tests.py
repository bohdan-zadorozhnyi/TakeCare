from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
from .forms import ChatRoomForm

User = get_user_model()

class ChatModelsTest(TestCase):
    def setUp(self):
        # Create two users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User One',
            phone_number='1234567890',
            personal_id='USER1111',
            birth_date='1990-01-01',
            gender='MALE',
            address='123 User St',
            role='PATIENT'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User Two',
            phone_number='0987654321',
            personal_id='USER2222',
            birth_date='1985-01-01',
            gender='FEMALE',
            address='456 User St',
            role='DOCTOR'
        )
        
        # Create a chat room
        self.chatroom = ChatRoom.objects.create(name=f"Chat between {self.user1.name} and {self.user2.name}")
        self.chatroom.participants.add(self.user1, self.user2)
        
        # Create a message
        self.message = Message.objects.create(
            chatroom=self.chatroom,
            sender=self.user1,
            content="Hello, this is a test message"
        )
    
    def test_chatroom_creation(self):
        """Test ChatRoom model creation and attributes"""
        self.assertEqual(self.chatroom.name, f"Chat between {self.user1.name} and {self.user2.name}")
        self.assertEqual(self.chatroom.participants.count(), 2)
        self.assertIn(self.user1, self.chatroom.participants.all())
        self.assertIn(self.user2, self.chatroom.participants.all())
    
    def test_chatroom_get_other_participant(self):
        """Test ChatRoom get_other_participant method"""
        other_participant = self.chatroom.get_other_participant(self.user1)
        self.assertEqual(other_participant, self.user2)
        
        other_participant = self.chatroom.get_other_participant(self.user2)
        self.assertEqual(other_participant, self.user1)
    
    def test_chatroom_get_participant_name(self):
        """Test ChatRoom get_participant_name method"""
        name = self.chatroom.get_participant_name(self.user1)
        self.assertEqual(name, "User One")
    
    def test_message_creation(self):
        """Test Message model creation and attributes"""
        self.assertEqual(self.message.sender, self.user1)
        self.assertEqual(self.message.content, "Hello, this is a test message")
        self.assertEqual(self.message.chatroom, self.chatroom)
    
    def test_message_str_representation(self):
        """Test Message string representation"""
        expected_str = f"{self.user1.name}: Hello, this is a test message"[:30]
        self.assertEqual(str(self.message), expected_str)
    
    def test_chatroom_str_representation(self):
        """Test ChatRoom string representation"""
        self.assertEqual(str(self.chatroom), self.chatroom.name)


class ChatFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User',
            phone_number='1234567890',
            personal_id='TEST1234',
            birth_date='1990-01-01',
            gender='MALE',
            address='123 Test St',
            role='PATIENT'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            name='Other User',
            phone_number='0987654321',
            personal_id='OTHER1234',
            birth_date='1985-01-01',
            gender='FEMALE',
            address='456 Other St',
            role='DOCTOR'
        )
    
    def test_chatroom_form_valid(self):
        """Test ChatRoomForm with valid data"""
        form = ChatRoomForm(user=self.user, data={'participant': self.other_user.id})
        self.assertTrue(form.is_valid())
    
    def test_chatroom_form_invalid(self):
        """Test ChatRoomForm with invalid data"""
        form = ChatRoomForm(user=self.user, data={'participant': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('participant', form.errors)


class ChatViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create two users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            name='User One',
            phone_number='1234567890',
            personal_id='USER1111',
            birth_date='1990-01-01',
            gender='MALE',
            address='123 User St',
            role='PATIENT'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            name='User Two',
            phone_number='0987654321',
            personal_id='USER2222',
            birth_date='1985-01-01',
            gender='FEMALE',
            address='456 User St',
            role='DOCTOR'
        )
        
        # Create a chat room
        self.chatroom = ChatRoom.objects.create(name=f"Chat between {self.user1.name} and {self.user2.name}")
        self.chatroom.participants.add(self.user1, self.user2)
        
        # Create messages
        Message.objects.create(
            chatroom=self.chatroom,
            sender=self.user1,
            content="Hello from user1"
        )
        
        Message.objects.create(
            chatroom=self.chatroom,
            sender=self.user2,
            content="Hello from user2"
        )
    
    def test_chat_list_view(self):
        """Test chat list view"""
        self.client.login(username='user1@example.com', password='testpass123')
        response = self.client.get(reverse('chatroom_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_chat_room_view(self):
        """Test chat room view"""
        self.client.login(username='user1@example.com', password='testpass123')
        response = self.client.get(reverse('chatroom_detail', args=[self.chatroom.id]))
        self.assertEqual(response.status_code, 200)
