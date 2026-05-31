import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.set_user_online(True)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_status',
            'user_id': self.user.id,
            'is_online': True,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            await self.set_user_online(False)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'user_status',
                'user_id': self.user.id,
                'is_online': False,
            })

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'chat_message')

        if msg_type == 'chat_message':
            content = data.get('message', '').strip()
            if not content:
                return
            message = await self.save_message(content)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'message': content,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'sender_avatar': self.user.get_avatar_url(),
                'message_id': message.id,
                'timestamp': message.timestamp.strftime('%H:%M'),
            })

            # 👇 notify the other user's home page
            other_user_id = await self.get_other_user_id()
            if other_user_id:
                await self.channel_layer.group_send(
                    f'user_{other_user_id}_notifications',
                    {
                        'type': 'new_message_notification',
                        'room_id': int(self.room_id),
                        'sender_username': self.user.username,
                        'sender_avatar': self.user.get_avatar_url(),
                        'message': content,
                        'timestamp': message.timestamp.strftime('%H:%M'),
                    }
                )

        elif msg_type in ('call_offer', 'call_answer', 'ice_candidate', 'call_end', 'call_rejected'):
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'webrtc_signal',
                'signal_type': msg_type,
                'data': data,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
            })

        elif msg_type == 'typing':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'typing_indicator',
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'is_typing': data.get('is_typing', False),
            })

        elif msg_type == 'mark_read':
            await self.mark_messages_read()

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'type': 'chat_message', **event}))

    async def webrtc_signal(self, event):
        if event.get('sender_id') != self.user.id:
            await self.send(text_data=json.dumps({'type': 'webrtc_signal', **event}))

    async def typing_indicator(self, event):
        if event.get('sender_id') != self.user.id:
            await self.send(text_data=json.dumps({'type': 'typing_indicator', **event}))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({'type': 'user_status', **event}))

    @database_sync_to_async
    def save_message(self, content):
        from .models import Room, Message
        room = Room.objects.get(id=self.room_id)
        return Message.objects.create(room=room, sender=self.user, content=content, message_type='text')

    @database_sync_to_async
    def set_user_online(self, status):
        from accounts.models import User
        User.objects.filter(id=self.user.id).update(is_online=status, last_seen=timezone.now())

    @database_sync_to_async
    def mark_messages_read(self):
        from .models import Room, Message
        room = Room.objects.get(id=self.room_id)
        Message.objects.filter(room=room, is_read=False).exclude(sender=self.user).update(is_read=True)

    @database_sync_to_async
    def get_other_user_id(self):
        from .models import Room
        room = Room.objects.get(id=self.room_id)
        other = room.participants.exclude(id=self.user.id).first()
        return other.id if other else None


class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = 'presence'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.set_online(True)

    async def disconnect(self, close_code):
        await self.set_online(False)
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def presence_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def set_online(self, status):
        from accounts.models import User
        User.objects.filter(id=self.user.id).update(is_online=status, last_seen=timezone.now())


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """Notifies home page of new messages in real time."""
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f'user_{self.user.id}_notifications'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def new_message_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            **event
        }))