from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.conf import settings
import logging
from .models import ChatRoom, Message
from .forms import ChatRoomForm
import json
import traceback

logger = logging.getLogger(__name__)

@login_required
def chatroom_list(request):
    chatrooms = ChatRoom.objects.filter(participants=request.user)
    form = ChatRoomForm(user=request.user)
    
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, user=request.user)
        if form.is_valid():
            other_user = form.cleaned_data['participant']
            # Create a new chat room
            chatroom = form.save(user=request.user)
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
    form = ChatRoomForm(user=request.user)
    other_participant = chatroom.get_other_participant(request.user)
    
    return render(request, 'chat/chatroom_detail.html', {
        'chatroom': chatroom,
        'chatrooms': chatrooms,
        'messages': messages,
        'form': form,
        'active_chat_id': room_id,
        'other_participant': other_participant,
        'other_participant_name': chatroom.get_participant_name(other_participant)
    })


@login_required
def send_message(request, room_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Only AJAX requests are allowed',
            'error_type': 'invalid_request'
        }, status=400)

    if request.method != 'POST':
        return JsonResponse({
            'error': 'This endpoint only accepts POST requests',
            'error_type': 'method_not_allowed'
        }, status=405)

    try:
        # Validate chat room access
        try:
            chatroom = ChatRoom.objects.get(id=room_id)
            if request.user not in chatroom.participants.all():
                return JsonResponse({
                    'error': 'You are not a participant in this chat room',
                    'error_type': 'permission_denied'
                }, status=403)
        except ChatRoom.DoesNotExist:
            return JsonResponse({
                'error': 'Chat room not found',
                'error_type': 'not_found'
            }, status=404)

        # Parse and validate request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data in request',
                'error_type': 'invalid_json'
            }, status=400)

        content = data.get('content')
        if not content or not content.strip():
            return JsonResponse({
                'error': 'Message content cannot be empty',
                'error_type': 'empty_content'
            }, status=400)

        # Create and save the message
        try:
            message = Message.objects.create(
                chatroom=chatroom,
                sender=request.user,
                content=content.strip()
            )
        except ValidationError as e:
            return JsonResponse({
                'error': str(e),
                'error_type': 'validation_error'
            }, status=400)
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}\n{traceback.format_exc()}")
            return JsonResponse({
                'error': 'Failed to save message',
                'error_type': 'database_error'
            }, status=500)

        # Return successful response
        return JsonResponse({
            'id': message.id,
            'sender': message.sender.name or f"User {message.sender.id}",
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Unexpected error in send_message: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': 'An unexpected error occurred',
            'error_type': 'server_error',
            'details': str(e) if settings.DEBUG else None
        }, status=500)
