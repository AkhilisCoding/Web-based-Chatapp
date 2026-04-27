from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from accounts.models import User
from .models import Room, Message
import json

@login_required
def home_view(request):
    rooms = request.user.rooms.prefetch_related('participants', 'messages').all()
    room_data = []
    for room in rooms:
        other = room.get_other_user(request.user)
        last_msg = room.get_last_message()
        unread = room.messages.filter(is_read=False).exclude(sender=request.user).count()
        room_data.append({
            'room': room,
            'other_user': other,
            'last_message': last_msg,
            'unread_count': unread,
        })
    return render(request, 'chat/home.html', {'rooms': room_data})

@login_required
def room_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if not room.participants.filter(id=request.user.id).exists():
        return redirect('chat:home')
    other_user = room.get_other_user(request.user)
    messages = room.messages.select_related('sender').all()
    # Mark messages as read
    room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'chat/room.html', {
        'room': room,
        'other_user': other_user,
        'messages': messages,
    })

@login_required
def start_chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        return redirect('chat:home')
    # Find existing room or create new one
    room = Room.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not room:
        room = Room.objects.create()
        room.participants.add(request.user, other_user)
    return redirect('chat:room', room_id=room.id)

@login_required
def search_users_view(request):
    query = request.GET.get('q', '').strip()
    users = []
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id).filter(is_verified=True)[:10]
    return render(request, 'chat/search.html', {'users': users, 'query': query})

@login_required
def upload_file_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        room_id = request.POST.get('room_id')
        room = get_object_or_404(Room, id=room_id)
        if not room.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        file = request.FILES['file']
        msg_type = 'image' if file.content_type.startswith('image/') else 'file'
        
        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=file.name,
            message_type=msg_type,
            file=file,
        )
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'file_url': message.file.url,
            'file_name': file.name,
            'message_type': msg_type,
            'sender_username': request.user.username,
            'timestamp': message.timestamp.strftime('%H:%M'),
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)
