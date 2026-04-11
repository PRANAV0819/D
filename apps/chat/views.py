import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Max, Prefetch

from apps.accounts.decorators import verified_required
from apps.accounts.models import User
from .models import ChatRoom, RoomMember, Message


# ── Helper: build annotated room list for the sidebar ────────────────

def build_room_list(user):
    """
    Returns a list of dicts for the sidebar. Optimised: avoids N+1 by
    prefetching memberships and using annotated querysets.
    """
    # Prefetch all memberships for this user in a single query
    memberships = {
        rm.room_id: rm
        for rm in RoomMember.objects.filter(user=user).select_related('room')
    }
    room_ids = list(memberships.keys())

    rooms = (
        ChatRoom.objects
        .filter(pk__in=room_ids)
        .prefetch_related(
            Prefetch(
                'members',
                queryset=User.objects.select_related('profile'),
            )
        )
        .annotate(last_msg_time=Max('messages__created_at'))
        .order_by('-last_msg_time')
    )

    # Batch fetch last messages for all rooms at once (SQLite-compatible)
    last_msgs = {}
    for msg in (
        Message.objects
        .filter(room_id__in=room_ids)
        .order_by('room_id', '-created_at')
        .select_related('sender')
    ):
        if msg.room_id not in last_msgs:
            last_msgs[msg.room_id] = msg

    result = []
    for room in rooms:
        last_msg   = last_msgs.get(room.pk) or room.messages.order_by('-created_at').first()
        membership = memberships[room.pk]
        unread     = membership.unread_count()

        if room.room_type == ChatRoom.RoomType.DM:
            other        = room.get_other_member(user)
            display_name = other.get_full_name() if other else 'Unknown'
            display_avatar = (
                other.profile.get_avatar_url()
                if other and hasattr(other, 'profile')
                else '/static/images/default-avatar.png'
            )
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

    raw_messages = room.messages.select_related('sender', 'sender__profile').all()

    # Annotate shared-post messages so the template doesn't do fragile string slicing
    import json as _json
    for msg in raw_messages:
        if msg.content.startswith('__SHARED_POST__'):
            msg.is_shared_post = True
            try:
                msg.shared_post_data = _json.loads(msg.content[15:])
            except Exception:
                msg.shared_post_data = {}
        else:
            msg.is_shared_post = False
            msg.shared_post_data = {}

    room_list = build_room_list(request.user)

    other = room.get_other_member(request.user) if room.room_type == ChatRoom.RoomType.DM else None

    return render(request, 'chat/chat.html', {
        'room_list':   room_list,
        'active_room': room,
        'messages':    raw_messages,
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


# ── AJAX: poll new messages (fallback if WebSocket fails) ────────────

@login_required
@verified_required
def poll_messages_view(request, room_id):
    """
    AJAX endpoint for polling new messages. Used as fallback when
    WebSocket is unavailable (e.g., proxy does not support WS).

    Query params:
        since_id  — return only messages with id > since_id
        mark_seen — if '1', mark fetched messages as seen

    Returns JSON: { messages: [...], user_id: int }
    """
    membership = get_object_or_404(RoomMember, room_id=room_id, user=request.user)
    room       = membership.room

    since_id = request.GET.get('since_id', 0)
    try:
        since_id = int(since_id)
    except (TypeError, ValueError):
        since_id = 0

    qs = (
        room.messages
        .select_related('sender', 'sender__profile')
        .filter(pk__gt=since_id)
        .order_by('created_at')
    )

    # Optionally mark as seen
    if request.GET.get('mark_seen') == '1':
        qs.exclude(sender=request.user).update(is_seen=True)
        RoomMember.objects.filter(room=room, user=request.user).update(last_read=timezone.now())

    data = []
    for msg in qs:
        try:
            avatar = msg.sender.profile.get_avatar_url()
        except Exception:
            avatar = '/static/images/default-avatar.png'

        data.append({
            'id':            msg.pk,
            'content':       msg.content,
            'sender_id':     msg.sender_id,
            'sender_name':   msg.sender.get_full_name(),
            'sender_avatar': avatar,
            'timestamp':     msg.created_at.strftime('%H:%M'),
            'is_seen':       msg.is_seen,
            'image_url':     msg.image.url if msg.image else None,
        })

    return JsonResponse({'messages': data, 'user_id': request.user.pk})


# ── AJAX: send a message (fallback when WebSocket is unavailable) ─────

@login_required
@verified_required
def send_message_view(request, room_id):
    """
    POST-only AJAX endpoint. Saves a message to the DB.
    Returns the saved message as JSON so the client can render it immediately.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    membership = get_object_or_404(RoomMember, room_id=room_id, user=request.user)
    room = membership.room

    from django.core.cache import cache
    
    # Rate Limiting: Max 10 messages per minute per user
    cache_key = f'chat_rate_limit_{request.user.pk}'
    msg_count = cache.get(cache_key, 0)
    if msg_count >= 10:
        return JsonResponse({'error': 'Rate limit exceeded. Please wait.'}, status=429)
    cache.set(cache_key, msg_count + 1, 60)

    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')
    
    if not content and not image:
        return JsonResponse({'error': 'empty message'}, status=400)

    from .models import Message
    msg = Message.objects.create(room=room, sender=request.user, content=content, image=image)

    try:
        avatar = request.user.profile.get_avatar_url()
    except Exception:
        avatar = '/static/images/default-avatar.png'

    return JsonResponse({
        'id':            msg.pk,
        'content':       msg.content,
        'sender_id':     request.user.pk,
        'sender_name':   request.user.get_full_name(),
        'sender_avatar': avatar,
        'timestamp':     msg.created_at.strftime('%H:%M'),
        'image_url':     msg.image.url if msg.image else None,
        'is_seen':       False,
    }, status=201)


# ── Delete a conversation ────────────────────────────────────────────

@login_required
@verified_required
def delete_room_view(request, room_id):
    """
    POST: Remove the current user from the room (soft-delete for the user).
    If no members remain after removal, delete the entire room too.
    """
    if request.method != 'POST':
        return redirect('chat:inbox')

    # Use filter().first() instead of get_object_or_404 out of precaution.
    # If the user clicks delete twice (or the request was interrupted halfway last time),
    # they shouldn't see a 404 error page. They are simply redirected.
    membership = RoomMember.objects.filter(room_id=room_id, user=request.user).first()
    
    if membership:
        room = membership.room
        membership.delete()

        # If no members remain, clean up the room entirely
        if not RoomMember.objects.filter(room=room).exists():
            room.delete()

        messages.success(request, 'Conversation deleted.')
        
    return redirect('chat:inbox')