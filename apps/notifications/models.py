from django.db import models
from django.conf import settings


class Notification(models.Model):

    class NotifType(models.TextChoices):
        CONNECTION = 'connection', 'Connection Request'
        MESSAGE    = 'message',    'New Message'
        JOB        = 'job',        'Job Update'
        MENTORSHIP = 'mentorship', 'Mentorship'
        PROJECT    = 'project',    'Project'
        EVENT      = 'event',      'Event'
        SYSTEM     = 'system',     'System'

    recipient  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    notif_type = models.CharField(max_length=20, choices=NotifType.choices, default=NotifType.SYSTEM)
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    link       = models.CharField(max_length=300, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Notif → {self.recipient.email}: {self.title}'

    @classmethod
    def send(cls, recipient, notif_type, title, message, link=''):
        """Helper to create a notification from anywhere in the codebase."""
        return cls.objects.create(
            recipient=recipient,
            notif_type=notif_type,
            title=title,
            message=message,
            link=link,
        )