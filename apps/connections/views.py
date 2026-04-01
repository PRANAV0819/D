from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import verified_required
from apps.accounts.models import User
from .models import Connection


# ── Network overview ───────────────────────────────────────────────────

@login_required
@verified_required
def network_view(request):
    """
    Three panels:
      - Pending incoming requests
      - Current connections
      - People you may know (same college, not yet connected)
    """
    user = request.user

    pending_received = Connection.objects.filter(
        receiver=user, status=Connection.Status.PENDING
    ).select_related('sender', 'sender__profile')

    pending_sent = Connection.objects.filter(
        sender=user, status=Connection.Status.PENDING
    ).values_list('receiver_id', flat=True)

    accepted = Connection.objects.filter(
        Q(sender=user) | Q(receiver=user),
        status=Connection.Status.ACCEPTED,
    ).select_related('sender', 'sender__profile', 'receiver', 'receiver__profile')

    # IDs to exclude from suggestions
    connected_ids = Connection.accepted_ids_for(user)
    excluded_ids  = connected_ids | set(pending_sent) | {user.pk}

    suggestions = (
        User.objects
        .filter(college=user.college, is_active=True, is_email_verified=True)
        .exclude(pk__in=excluded_ids)
        .select_related('profile')
        .order_by('?')[:12]
    )

    return render(request, 'connections/network.html', {
        'pending_received': pending_received,
        'pending_sent_ids': set(pending_sent),
        'accepted':         accepted,
        'suggestions':      suggestions,
    })


# ── Send connection request ────────────────────────────────────────────

@login_required
@verified_required
@require_POST
def send_request_view(request, user_id):
    receiver = get_object_or_404(User, pk=user_id, is_active=True)

    if receiver == request.user:
        messages.error(request, "You can't connect with yourself.")
        return redirect('connections:network')

    existing = Connection.get_status_between(request.user, receiver)
    if existing:
        messages.info(request, 'A connection request already exists between you and this user.')
        return redirect('connections:network')

    Connection.objects.create(sender=request.user, receiver=receiver)
    messages.success(request, f'Connection request sent to {receiver.get_full_name()}.')
    return redirect(request.META.get('HTTP_REFERER', 'connections:network'))


# ── Accept request ─────────────────────────────────────────────────────

@login_required
@verified_required
@require_POST
def accept_request_view(request, connection_id):
    conn = get_object_or_404(
        Connection, pk=connection_id, receiver=request.user, status=Connection.Status.PENDING
    )
    conn.status = Connection.Status.ACCEPTED
    conn.save()
    messages.success(request, f'You are now connected with {conn.sender.get_full_name()}.')
    return redirect(request.META.get('HTTP_REFERER', 'connections:network'))


# ── Reject / withdraw request ──────────────────────────────────────────

@login_required
@verified_required
@require_POST
def reject_request_view(request, connection_id):
    conn = get_object_or_404(Connection, pk=connection_id)

    # Either the receiver rejects OR the sender withdraws
    if conn.receiver == request.user or conn.sender == request.user:
        other = conn.sender if conn.receiver == request.user else conn.receiver
        conn.delete()
        messages.info(request, f'Connection request with {other.get_full_name()} removed.')
    else:
        messages.error(request, 'Permission denied.')

    return redirect(request.META.get('HTTP_REFERER', 'connections:network'))


# ── Remove connection ──────────────────────────────────────────────────

@login_required
@verified_required
@require_POST
def remove_connection_view(request, user_id):
    other = get_object_or_404(User, pk=user_id)
    conn  = Connection.get_status_between(request.user, other)

    if conn and conn.status == Connection.Status.ACCEPTED:
        conn.delete()
        messages.info(request, f'Removed connection with {other.get_full_name()}.')
    else:
        messages.error(request, 'No active connection found.')

    return redirect(request.META.get('HTTP_REFERER', 'connections:network'))


# ── People search ──────────────────────────────────────────────────────

@login_required
@verified_required
def people_search_view(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = (
            User.objects
            .filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)  |
                Q(email__icontains=query),
                is_active=True,
                is_email_verified=True,
            )
            .exclude(pk=request.user.pk)
            .select_related('profile', 'college', 'department')[:20]
        )

        # Annotate each result with the connection status
        for person in results:
            conn = Connection.get_status_between(request.user, person)
            if conn is None:
                person.conn_status = 'none'
                person.conn_id     = None
            else:
                person.conn_status = conn.status
                person.conn_id     = conn.pk

    return render(request, 'connections/people_search.html', {
        'results': results,
        'query':   query,
    })


# ── AJAX: connection status (used by profile buttons) ─────────────────

@login_required
def connection_status_view(request, user_id):
    other = get_object_or_404(User, pk=user_id)
    conn  = Connection.get_status_between(request.user, other)
    return JsonResponse({
        'status': conn.status if conn else 'none',
        'conn_id': conn.pk   if conn else None,
        'is_sender': conn.sender_id == request.user.pk if conn else None,
    })