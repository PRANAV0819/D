from django.db import models
from django.conf import settings


class MarketplaceItem(models.Model):

    class Condition(models.TextChoices):
        NEW       = 'new',       'New'
        LIKE_NEW  = 'like_new',  'Like New'
        GOOD      = 'good',      'Good'
        FAIR      = 'fair',      'Fair'

    class ItemStatus(models.TextChoices):
        ACTIVE   = 'active',   'Active'
        RESERVED = 'reserved', 'Reserved'
        SOLD     = 'sold',     'Sold'

    seller      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='marketplace_items'
    )
    title       = models.CharField(max_length=200)
    description = models.TextField()
    price       = models.DecimalField(max_digits=8, decimal_places=2)
    condition   = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)
    image       = models.ImageField(upload_to='marketplace/', blank=True, null=True)
    status      = models.CharField(max_length=20, choices=ItemStatus.choices, default=ItemStatus.ACTIVE)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title