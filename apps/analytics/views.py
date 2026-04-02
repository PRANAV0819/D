from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from apps.accounts.decorators import verified_required
from apps.gamification.models import UserActivity
from apps.connections.models import Connection
from apps.social.models import Post


@login_required
@verified_required
def analytics_view(request):
    user = request.user

    # Activity heatmap — last 365 days
    today = timezone.now().date()
    year_ago = today - timedelta(days=364)
    activity_qs = (
        UserActivity.objects
        .filter(user=user, activity_date__gte=year_ago)
        .values('activity_date')
        .annotate(count=Count('id'))
    )
    activity_map = {str(row['activity_date']): row['count'] for row in activity_qs}

    # Build 52-week grid
    weeks = []
    day_cursor = year_ago - timedelta(days=year_ago.weekday())
    for _ in range(53):
        week = []
        for d in range(7):
            day = day_cursor + timedelta(days=d)
            count = activity_map.get(str(day), 0)
            week.append({'date': str(day), 'count': count})
        weeks.append(week)
        day_cursor += timedelta(weeks=1)

    # Stats
    conn_count  = Connection.objects.filter(
        __import__('django.db.models', fromlist=['Q']).Q(sender=user) |
        __import__('django.db.models', fromlist=['Q']).Q(receiver=user),
        status='accepted'
    ).count()
    post_count  = Post.objects.filter(author=user).count()
    total_pts   = user.profile.points
    streak      = user.profile.streak_days

    # Skill distribution (for chart)
    user_skills = user.user_skills.select_related('skill').all()

    return render(request, 'analytics/dashboard.html', {
        'weeks':       weeks,
        'conn_count':  conn_count,
        'post_count':  post_count,
        'total_pts':   total_pts,
        'streak':      streak,
        'user_skills': user_skills,
        'today':       str(today),
    })