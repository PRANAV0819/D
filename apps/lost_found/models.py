from django.db import models
from django.conf import settings


class LostFoundItem(models.Model):

    class ItemType(models.TextChoices):
        LOST  = 'lost',  'Lost'
        FOUND = 'found', 'Found'

    class ItemStatus(models.TextChoices):
        OPEN    = 'open',    'Open'
        CLAIMED = 'claimed', 'Claimed/Resolved'

    posted_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lostfound_posts'
    )
    item_type   = models.CharField(max_length=10, choices=ItemType.choices)
    title       = models.CharField(max_length=200)
    description = models.TextField()
    location    = models.CharField(max_length=200, blank=True)
    image       = models.ImageField(upload_to='lost_found/', blank=True, null=True)
    status      = models.CharField(max_length=20, choices=ItemStatus.choices, default=ItemStatus.OPEN)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.item_type.upper()}] {self.title}'