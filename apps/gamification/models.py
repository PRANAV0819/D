from django.db import models
from django.conf import settings


class Badge(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon        = models.CharField(max_length=50, default='bi-award-fill', help_text='Bootstrap icon class')
    color       = models.CharField(max_length=30, default='gh-tag-amber')
    points_required = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge     = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f'{self.user.email} — {self.badge.name}'


class UserActivity(models.Model):

    class Action(models.TextChoices):
        POST        = 'post',        'Created a post'
        COMMENT     = 'comment',     'Commented'
        LIKE        = 'like',        'Liked a post'
        CONNECT     = 'connect',     'Made a connection'
        JOB_APPLY   = 'job_apply',   'Applied for a job'
        UPLOAD      = 'upload',      'Uploaded resource'
        PROJECT     = 'project',     'Joined a project'
        LOGIN       = 'login',       'Daily login'
        STREAK_UPDATE = 'streak_update', 'Updated streak'

    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    action        = models.CharField(max_length=30, choices=Action.choices)
    points_earned = models.PositiveSmallIntegerField(default=0)
    activity_date = models.DateField(auto_now_add=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    # Points per action
    POINTS_MAP = {
        'post': 10, 'comment': 5, 'like': 2,
        'connect': 8, 'job_apply': 15, 'upload': 12,
        'project': 20, 'login': 3,
        'streak_update': 10,
    }

    @classmethod
    def log(cls, user, action):
        points = cls.POINTS_MAP.get(action, 0)
        instance = cls.objects.create(user=user, action=action, points_earned=points)
        # Update profile points
        from apps.accounts.models import Profile
        Profile.objects.filter(user=user).update(points=models.F('points') + points)
        # Check badge thresholds
        cls._check_badges(user)
        return instance

    @classmethod
    def _check_badges(cls, user):
        from apps.accounts.models import Profile
        profile = Profile.objects.get(user=user)
        for badge in Badge.objects.all():
            if profile.points >= badge.points_required:
                UserBadge.objects.get_or_create(user=user, badge=badge)