from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Max

from apps.accounts.decorators import verified_required
from apps.accounts.models import User
from .models import ChatRoom, RoomMember, Message


# ── Helper: build annotated room list for the sidebar ────────────────

def build_room_list(user):
    room_ids = RoomMember.objects.filter(user=user).values_list('room_id', flat=True)
    rooms    = (
        ChatRoom.objects
        .filter(pk__in=room_ids)
        .prefetch_related('members', 'members__profile')
        .annotate(last_msg_time=Max('messages__created_at'))
        .order_by('-last_msg_time')
    )

    result = []
    for room in rooms:
        last_msg   = room.messages.order_by('-created_at').first()
        membership = RoomMember.objects.get(room=room, user=user)
        unread     = membership.unread_count()

        if room.room_type == ChatRoom.RoomType.DM:
            other        = room.get_other_member(user)
            display_name = other.get_full_name() if other else 'Unknown'
            display_avatar = other.profile.get_avatar_url() if other else '/static/images/default-avatar.png'
        else:
            other          = None
            display_name   = room.name or f'Group #{room.pk}'
            display_avatar = '/static/images/default-avatar.png'

        result.append({
            'room':           room,
            'last_message':   last_msg,
            'unread':         unread,
            'other':          other,
            'display_name':   display_name,
            'display_avatar': display_avatar,
        })
    return result


# ── Inbox (no active room) ────────────────────────────────────────────

@login_required
@verified_required
def inbox_view(request):
    room_list = build_room_list(request.user)
    return render(request, 'chat/chat.html', {
        'room_list':   room_list,
        'active_room': None,
        'messages':    [],
        'other':       None,
    })


# ── Active room ───────────────────────────────────────────────────────

@login_required
@verified_required
def room_view(request, room_id):
    # Ensure the user is a member
    membership = get_object_or_404(RoomMember, room_id=room_id, user=request.user)
    room       = membership.room

    # Mark messages as read on HTTP load (WS also does this on connect)
    Message.objects.filter(
        room=room, is_seen=False
    ).exclude(sender=request.user).update(is_seen=True)
    RoomMember.objects.filter(room=room, user=request.user).update(last_read=timezone.now())

    messages  = room.messages.select_related('sender', 'sender__profile').all()
    room_list = build_room_list(request.user)

    other = room.get_other_member(request.user) if room.room_type == ChatRoom.RoomType.DM else None

    return render(request, 'chat/chat.html', {
        'room_list':   room_list,
        'active_room': room,
        'messages':    messages,
        'other':       other,
    })


# ── Create or get DM, redirect to room ───────────────────────────────

@login_required
@verified_required
def create_dm_view(request, user_id):
    other = get_object_or_404(User, pk=user_id, is_active=True)

    if other == request.user:
        return redirect('chat:inbox')

    room, _ = ChatRoom.get_or_create_dm(request.user, other)
    return redirect('chat:room', room_id=room.pk)