from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import ChatRoom, Message
from .forms import ChatRoomForm
from django.conf import settings
import json


@login_required
def chatroom_list(request):
    chatrooms = ChatRoom.objects.filter(participants=request.user)
    form = ChatRoomForm()
    
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            chatroom = form.save()
            chatroom.participants.add(request.user)  # Add the creator as a participant
            return redirect('chatroom_detail', room_id=chatroom.id)
    
    return render(request, 'chat/chatroom_list.html', {
        'chatrooms': chatrooms,
        'form': form,
        'active_chat_id': None
    })


@login_required
def chatroom_detail(request, room_id):
    chatroom = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    chatrooms = ChatRoom.objects.filter(participants=request.user)
    messages = chatroom.messages.order_by('timestamp')
    form = ChatRoomForm()
    
    return render(request, 'chat/chatroom_detail.html', {
        'chatroom': chatroom,
        'chatrooms': chatrooms,
        'messages': messages,
        'form': form,
        'active_chat_id': room_id
    })


@csrf_exempt
@login_required
def send_message(request, room_id):
    if request.method == 'POST':
        try:
            chatroom = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
            data = json.loads(request.body)
            content = data.get('content')
            
            if not content:
                return JsonResponse({
                    'error': 'Message content cannot be empty'
                }, status=400)
            
            message = Message.objects.create(
                chatroom=chatroom,
                sender=request.user,
                content=content
            )
            
            return JsonResponse({
                'id': message.id,
                'sender': message.sender.username,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': 'An error occurred while sending the message'
            }, status=500)
            
    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)
