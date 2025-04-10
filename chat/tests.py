
from django.test import TestCase, Client, TransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .routing import websocket_urlpatterns
from .models import ChatRoom, Message
from .consumers import ChatConsumer
import json
from datetime import date
import pytest

User = get_user_model()

class ChatModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='pass123',
            name='User One',
            phone_number='+1234567890',
            personal_id='ID12345',
            birth_date=date(1990, 1, 1),
            gender='MALE',
            address='123 Street',
            role='PATIENT'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='pass123',
            name='User Two',
            phone_number='+0987654321',
            personal_id='ID67890',
            birth_date=date(1990, 1, 1),
            gender='FEMALE',
            address='456 Avenue',
            role='DOCTOR'
        )
        
    def test_chatroom_creation(self):
        chatroom = ChatRoom.objects.create(name="Test Chat")
        chatroom.participants.add(self.user1, self.user2)
        self.assertEqual(chatroom.participants.count(), 2)
        
    def test_chatroom_validation(self):
        chatroom = ChatRoom.objects.create(name="Test Chat")
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='pass123',
            name='User Three',
            phone_number='+1122334455',
            personal_id='ID11223',
            birth_date=date(1990, 1, 1),
            gender='OTHER',
            address='789 Road',
            role='PATIENT'
        )
        
        chatroom.participants.add(self.user1, self.user2)
        with self.assertRaises(ValidationError):
            chatroom.participants.add(user3)
            chatroom.clean()
            
    def test_message_creation(self):
        chatroom = ChatRoom.objects.create(name="Test Chat")
        chatroom.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            chatroom=chatroom,
            sender=self.user1,
            content="Hello, World!"
        )
        self.assertEqual(message.content, "Hello, World!")
        self.assertEqual(message.sender, self.user1)

class ChatViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='pass123',
            name='User One',
            phone_number='+1234567890',
            personal_id='ID12345',
            birth_date=date(1990, 1, 1),
            gender='MALE',
            address='123 Street',
            role='PATIENT'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='pass123',
            name='User Two',
            phone_number='+0987654321',
            personal_id='ID67890',
            birth_date=date(1990, 1, 1),
            gender='FEMALE',
            address='456 Avenue',
            role='DOCTOR'
        )
        self.client.login(username=self.user1.email, password='pass123')
        
    def test_chatroom_list_view(self):
        response = self.client.get(reverse('chatroom_list'))
        self.assertEqual(response.status_code, 200)
        
    def test_chatroom_creation_view(self):
        data = {'participant': self.user2.id}
        response = self.client.post(reverse('chatroom_list'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertEqual(ChatRoom.objects.count(), 1)
        
    def test_chatroom_detail_view(self):
        chatroom = ChatRoom.objects.create(name="Test Chat")
        chatroom.participants.add(self.user1, self.user2)
        response = self.client.get(reverse('chatroom_detail', kwargs={'room_id': chatroom.id}))
        self.assertEqual(response.status_code, 200)

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class ChatConsumerTests(TransactionTestCase):
    async def test_chat_consumer_connection(self):
        self.user = await database_sync_to_async(User.objects.create_user)(
            email='testuser@example.com',
            password='testpass',
            name='Test User',
            phone_number='+9876543210',
            personal_id='ID99999',
            birth_date=date(1990, 1, 1),
            gender='MALE',
            address='Test Address',
            role='PATIENT'
        )
        self.chatroom = await database_sync_to_async(ChatRoom.objects.create)(name="Test Chat")
        await database_sync_to_async(self.chatroom.participants.add)(self.user)
        
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.chatroom.id}/",
        )
        communicator.scope["user"] = self.user
        connected, _ = await communicator.connect()
        
        assert connected
        await communicator.disconnect()
        
    async def test_chat_consumer_message(self):
        self.user = await database_sync_to_async(User.objects.create_user)(
            email='testuser@example.com',
            password='testpass',
            name='Test User',
            phone_number='+9876543210',
            personal_id='ID99999',
            birth_date=date(1990, 1, 1),
            gender='MALE',
            address='Test Address',
            role='PATIENT'
        )
        self.chatroom = await database_sync_to_async(ChatRoom.objects.create)(name="Test Chat")
        await database_sync_to_async(self.chatroom.participants.add)(self.user)
        
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.chatroom.id}/",
        )
        communicator.scope["user"] = self.user
        connected, _ = await communicator.connect()
        assert connected
        
        # Test sending message
        await communicator.send_json_to({
            "message": "Hello, World!"
        })
        
        # Test receiving message
        response = await communicator.receive_json_from()
        assert response["message"] == "Hello, World!"
        assert response["sender_id"] == str(self.user.id)
        
        await communicator.disconnect()
