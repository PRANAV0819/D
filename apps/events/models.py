from django.db import models
from django.conf import settings


class Event(models.Model):

    class EventType(models.TextChoices):
        HACKATHON = 'hackathon', 'Hackathon'
        WEBINAR   = 'webinar',   'Webinar'
        WORKSHOP  = 'workshop',  'Workshop'
        SEMINAR   = 'seminar',   'Seminar'
        CONTEST   = 'contest',   'Contest'
        OTHER     = 'other',     'Other'

    organizer    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organized_events'
    )
    title        = models.CharField(max_length=200)
    event_type   = models.CharField(max_length=20, choices=EventType.choices, default=EventType.WEBINAR)
    description  = models.TextField()
    banner       = models.ImageField(upload_to='events/banners/', blank=True, null=True)
    location     = models.CharField(max_length=300, blank=True, help_text='Physical address or meeting link')
    starts_at    = models.DateTimeField()
    ends_at      = models.DateTimeField(null=True, blank=True)
    registration_link = models.URLField(blank=True)
    max_participants  = models.PositiveIntegerField(null=True, blank=True)
    is_online    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    registrations = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='EventRegistration', related_name='registered_events'
    )

    class Meta:
        ordering = ['starts_at']

    def __str__(self):
        return self.title

    def registration_count(self):
        return self.registrations.count()


class EventRegistration(models.Model):
    event       = models.ForeignKey(Event, on_delete=models.CASCADE)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')