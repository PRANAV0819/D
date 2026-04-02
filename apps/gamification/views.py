from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.accounts.decorators import verified_required
from apps.accounts.models import User
from .models import Badge, UserBadge, UserActivity


@login_required
@verified_required
def leaderboard_view(request):
    top_users = (
        User.objects.filter(is_active=True, is_email_verified=True)
        .select_related('profile')
        .order_by('-profile__points')[:20]
    )
    my_badges    = UserBadge.objects.filter(user=request.user).select_related('badge')
    all_badges   = Badge.objects.all()
    my_badge_ids = set(my_badges.values_list('badge_id', flat=True))
    recent_activity = UserActivity.objects.filter(user=request.user)[:10]
    return render(request, 'gamification/leaderboard.html', {
        'top_users':        top_users,
        'my_badges':        my_badges,
        'all_badges':       all_badges,
        'my_badge_ids':     my_badge_ids,
        'recent_activity':  recent_activity,
    })