from django.db import models
from django.conf import settings


class MentorProfile(models.Model):
    user       = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile'
    )
    expertise  = models.TextField(help_text='Comma-separated topics, e.g. Machine Learning, Career, DSA')
    experience = models.PositiveIntegerField(default=0, help_text='Years of experience')
    bio        = models.TextField(blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Mentor: {self.user.get_full_name()}'

    def expertise_list(self):
        return [e.strip() for e in self.expertise.split(',') if e.strip()]


class MentorshipRequest(models.Model):

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED= 'completed','Completed'

    mentee     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_requests'
    )
    mentor     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_received'
    )
    message    = models.TextField(max_length=500, help_text='Why do you want this mentor?')
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mentee', 'mentor')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.mentee} → {self.mentor} [{self.status}]'


class MentorSession(models.Model):

    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    request      = models.ForeignKey(
        MentorshipRequest, on_delete=models.CASCADE, related_name='sessions'
    )
    title        = models.CharField(max_length=200, blank=True)
    scheduled_at = models.DateTimeField()
    duration_min = models.PositiveIntegerField(default=60)
    meeting_link = models.URLField(blank=True)
    notes        = models.TextField(blank=True)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'Session: {self.request.mentee} with {self.request.mentor}'