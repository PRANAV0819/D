from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime

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
    month_labels = []
    last_month = -1

    for week_idx in range(53):
        week = []
        week_first_day = None
        for d in range(7):
            day = day_cursor + timedelta(days=d)
            if week_first_day is None:
                week_first_day = day
            count = activity_map.get(str(day), 0)
            week.append({'date': str(day), 'count': count})
        weeks.append(week)
        
        # Calculate month label positions
        if week_first_day.month != last_month and week_first_day.day <= 7:
            month_labels.append({
                'name': week_first_day.strftime('%b'), 
                'col_index': week_idx
            })
            last_month = week_first_day.month
            
        day_cursor += timedelta(weeks=1)

    # Check if user updated streak today
    streak_updated_today = UserActivity.objects.filter(
        user=user, 
        action='STREAK_UPDATE', 
        activity_date=today
    ).exists()

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
    user_skills = user.profile.profile_skills.select_related('skill').all()

    return render(request, 'analytics/dashboard.html', {
        'weeks':                weeks,
        'month_labels':         month_labels,
        'conn_count':           conn_count,
        'post_count':           post_count,
        'total_pts':            total_pts,
        'streak':               streak,
        'user_skills':          user_skills,
        'today':                str(today),
        'streak_updated_today': streak_updated_today,
    })


@login_required
@verified_required
def update_streak_view(request):
    if request.method == 'POST':
        user = request.user
        today = timezone.now().date()
        
        # Check if already updated today
        already_updated = UserActivity.objects.filter(
            user=user, 
            action='STREAK_UPDATE', 
            activity_date=today
        ).exists()
        
        if not already_updated:
            UserActivity.objects.create(
                user=user,
                action='STREAK_UPDATE',
                activity_date=today,
                points_awarded=10
            )
            user.profile.points += 10
            user.profile.streak_days += 1
            user.profile.save()
            messages.success(request, 'Streak updated! +10 points.')
        else:
            messages.info(request, 'You already updated your streak today.')
            
    return redirect('analytics:dashboard')