from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, Sum
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime

from apps.accounts.decorators import verified_required
from apps.accounts.models import User
from apps.gamification.models import UserActivity
from apps.connections.models import Connection
from apps.social.models import Post, Comment, Like
from apps.mentorship.models import MentorshipRequest, MentorSession
from apps.marketplace.models import MarketplaceItem
from apps.lost_found.models import LostFoundItem
from apps.projects.models import Project, ProjectMember
from apps.resources.models import Resource


@login_required
@verified_required
def analytics_view(request):
    user = request.user

    # Activity heatmap — Calendar Year (Jan to Dec)
    today = timezone.now().date()
    try:
        display_year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        display_year = today.year

    start_of_year = datetime(display_year, 1, 1).date()
    end_of_year   = datetime(display_year, 12, 31).date()

    activity_qs = (
        UserActivity.objects
        .filter(user=user, activity_date__range=(start_of_year, end_of_year))
        .values('activity_date')
        .annotate(count=Count('id'))
    )
    activity_map = {str(row['activity_date']): row['count'] for row in activity_qs}

    # Build 52-week grid (covering the full calendar year)
    weeks = []
    day_cursor = start_of_year - timedelta(days=start_of_year.weekday())
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
        if week_idx == 0:
            month_labels.append({
                'name': 'Jan', 
                'col_index': 0
            })
            last_month = 1 # Jan label already present
        elif week_first_day.month != last_month and week_first_day.day <= 7:
            month_labels.append({
                'name': week_first_day.strftime('%b'), 
                'col_index': week_idx
            })
            last_month = week_first_day.month
            
        day_cursor += timedelta(weeks=1)

    # Check if user updated streak today
    streak_updated_today = UserActivity.objects.filter(
        user=user, 
        action='streak_update', 
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
    user_skills = user.profile.profile_skills.select_related('skill').all()

    # --- Module-wise Aggregation ---
    mentee_requests = MentorshipRequest.objects.filter(mentee=user).count()
    mentor_requests = MentorshipRequest.objects.filter(mentor=user).count()
    mentor_sessions = MentorSession.objects.filter(Q(request__mentee=user) | Q(request__mentor=user), status='completed').count()
    
    # Marketplace stats
    market_posts = MarketplaceItem.objects.filter(seller=user).count()
    items_sold   = MarketplaceItem.objects.filter(seller=user, status='sold').count()

    lf_reports = LostFoundItem.objects.filter(posted_by=user).count()
    lf_resolved= LostFoundItem.objects.filter(posted_by=user, status='claimed').count()

    projects_created = Project.objects.filter(owner=user).count()
    projects_joined  = ProjectMember.objects.filter(user=user).count()

    resources_count = Resource.objects.filter(uploaded_by=user).count()
    
    # --- Performance Metrics ---
    total_users = User.objects.filter(is_active=True).count()
    rank = User.objects.filter(profile__points__gt=user.profile.points).count() + 1
    percentile = round((1 - rank / total_users) * 100, 1) if total_users > 0 else 100

    # Engagement Score (Weighted)
    # Weights: Mentorship=15, Projects=10, Marketplace/LF=5, Resources=8, Social=2
    engagement_score = (
        (mentor_sessions * 15) + 
        (projects_joined * 10) + 
        (market_posts * 5) + 
        (resources_count * 8) + 
        (post_count * 2) + 
        (streak * 3)
    )
    
    # Contribution Level
    if engagement_score < 50:
        contrib_level = "Low"
        contrib_class = "gh-tag-secondary"
    elif engagement_score < 200:
        contrib_level = "Medium"
        contrib_class = "gh-tag-blue"
    else:
        contrib_level = "High"
        contrib_class = "gh-tag-amber"

    # Recent Activity Timeline
    recent_events = UserActivity.objects.filter(user=user).order_by('-created_at')[:8]

    # Suggestions
    suggestions = []
    if mentor_sessions < 2:
        suggestions.append("Increase participation in mentorship to gain professional insights.")
    if projects_joined == 0:
        suggestions.append("Collaborate on a project to build your portfolio.")
    if resources_count < 3:
        suggestions.append("Share valuable resources with your peers to boost your reputation.")
    if streak < 3:
        suggestions.append("Keep a daily streak to stay engaged with the community.")

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
        'display_year':         display_year,
        'prev_year':            display_year - 1,
        'next_year':            display_year + 1,
        
        # New Metrics
        'mentorship_stats':     {'sessions': mentor_sessions, 'requests': mentee_requests + mentor_requests},
        'marketplace_stats':    {'posts': market_posts, 'sold': items_sold},
        'lost_found_stats':     {'reports': lf_reports, 'resolved': lf_resolved},
        'project_stats':        {'created': projects_created, 'joined': projects_joined},
        'resource_stats':       {'uploads': resources_count},
        'performance': {
            'rank': rank,
            'percentile': percentile,
            'engagement_score': engagement_score,
            'contrib_level': contrib_level,
            'contrib_class': contrib_class,
            'profile_views': user.profile.profile_views
        },
        'recent_events': recent_events,
        'suggestions': suggestions[:3], # Show top 3 suggestions
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
            action='streak_update', 
            activity_date=today
        ).exists()
        
        if not already_updated:
            from apps.gamification.models import UserActivity
            UserActivity.log(user, UserActivity.Action.STREAK_UPDATE)
            
            user.profile.streak_days += 1
            user.profile.save()
            messages.success(request, 'Streak updated! +10 points.')
        else:
            messages.info(request, 'You already updated your streak today.')
            
    return redirect('analytics:dashboard')