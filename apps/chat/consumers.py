import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):

    # ── Lifecycle ──────────────────────────────────────────────────────

    async def connect(self):
        self.user    = self.scope['user']
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.group   = f'chat_{self.room_id}'

        # Reject unauthenticated or non-members
        if not self.user.is_authenticated:
            await self.close()
            return

        is_member = await self.check_membership()
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        # Mark existing messages as seen on connect
        await self.mark_messages_seen()

        # Broadcast online presence
        await self.channel_layer.group_send(self.group, {
            'type':    'user_online',
            'user_id': self.user.pk,
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'group'):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    # ── Receive from WebSocket client ─────────────────────────────────

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type', 'chat_message')

        if msg_type == 'chat_message':
            content = data.get('content', '').strip()
            if not content:
                return
            payload = await self.save_message(content)
            await self.channel_layer.group_send(self.group, {
                'type': 'chat_message',
                **payload,
            })

        elif msg_type == 'typing':
            await self.channel_layer.group_send(self.group, {
                'type':         'typing_indicator',
                'sender_id':    self.user.pk,
                'sender_name':  self.user.first_name,
                'is_typing':    data.get('is_typing', False),
            })

        elif msg_type == 'seen':
            await self.mark_messages_seen()
            await self.channel_layer.group_send(self.group, {
                'type':    'messages_seen',
                'user_id': self.user.pk,
            })

    # ── Handlers (called by group_send → sent to WebSocket clients) ───

    async def chat_message(self, event):
        """Broadcast a new message to all room members."""
        await self.send(text_data=json.dumps({
            'type':          'chat_message',
            'message_id':    event['message_id'],
            'content':       event['content'],
            'sender_id':     event['sender_id'],
            'sender_name':   event['sender_name'],
            'sender_avatar': event['sender_avatar'],
            'timestamp':     event['timestamp'],
        }))

    async def typing_indicator(self, event):
        """Forward typing state — skip sending back to the typer."""
        if event['sender_id'] == self.user.pk:
            return
        await self.send(text_data=json.dumps({
            'type':        'typing',
            'sender_name': event['sender_name'],
            'is_typing':   event['is_typing'],
        }))

    async def messages_seen(self, event):
        """Notify clients that messages have been read."""
        await self.send(text_data=json.dumps({
            'type':    'seen',
            'user_id': event['user_id'],
        }))

    async def user_online(self, event):
        """Notify room that a member is online."""
        if event['user_id'] == self.user.pk:
            return
        await self.send(text_data=json.dumps({
            'type':    'online',
            'user_id': event['user_id'],
        }))

    # ── DB helpers (sync → async bridge) ──────────────────────────────

    @database_sync_to_async
    def check_membership(self):
        from .models import RoomMember
        return RoomMember.objects.filter(
            room_id=self.room_id, user=self.user
        ).exists()

    @database_sync_to_async
    def save_message(self, content):
        """Save message to DB and return the broadcast payload dict."""
        from .models import Message, ChatRoom
        from apps.accounts.models import Profile

        room = ChatRoom.objects.get(pk=self.room_id)
        msg  = Message.objects.create(
            room=room, sender=self.user, content=content
        )

        try:
            avatar = Profile.objects.get(user=self.user).get_avatar_url()
        except Profile.DoesNotExist:
            avatar = '/static/images/default-avatar.png'

        return {
            'message_id':    msg.pk,
            'content':       msg.content,
            'sender_id':     self.user.pk,
            'sender_name':   self.user.get_full_name(),
            'sender_avatar': avatar,
            'timestamp':     msg.created_at.strftime('%H:%M'),
        }

    @database_sync_to_async
    def mark_messages_seen(self):
        from .models import Message, RoomMember
        now = timezone.now()
        Message.objects.filter(
            room_id=self.room_id, is_seen=False
        ).exclude(sender=self.user).update(is_seen=True)
        RoomMember.objects.filter(
            room_id=self.room_id, user=self.user
        ).update(last_read=now)