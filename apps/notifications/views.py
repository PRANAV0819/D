from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from apps.accounts.decorators import verified_required
from .models import Notification


@login_required
@verified_required
def notification_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    # Mark all as read on page visit
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def unread_count_view(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def mark_read_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications:list')