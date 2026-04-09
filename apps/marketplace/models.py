from django.db import models
from django.conf import settings


class MarketplaceItem(models.Model):

    class Condition(models.TextChoices):
        NEW       = 'new',       'New'
        LIKE_NEW  = 'like_new',  'Like New'
        GOOD      = 'good',      'Good'
        FAIR      = 'fair',      'Fair'

    class MarketplaceCategory(models.TextChoices):
        ELECTRONICS = 'electronics', 'Electronics'
        BOOKS       = 'books',       'Books & Notes'
        FURNITURE   = 'furniture',   'Furniture'
        CLOTHING    = 'clothing',    'Clothing'
        OTHER       = 'other',       'Other'

    class ItemStatus(models.TextChoices):
        ACTIVE   = 'active',   'Available'
        RESERVED = 'reserved', 'Reserved'
        SOLD     = 'sold',     'Sold'

    seller      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='marketplace_items'
    )
    title       = models.CharField(max_length=200)
    description = models.TextField()
    price       = models.DecimalField(max_digits=8, decimal_places=2)
    condition   = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)
    category    = models.CharField(max_length=30, choices=MarketplaceCategory.choices, default=MarketplaceCategory.OTHER)
    location    = models.CharField(max_length=150, blank=True, help_text="e.g., Hostel Block A, Room 102")
    image       = models.ImageField(upload_to='marketplace/', blank=True, null=True)
    status      = models.CharField(max_length=20, choices=ItemStatus.choices, default=ItemStatus.ACTIVE)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class OrderRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'

    item = models.ForeignKey(MarketplaceItem, on_delete=models.CASCADE, related_name='order_requests')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buy_requests')
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    message = models.TextField(blank=True, help_text="Optional message to seller")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('item', 'buyer')

    def __str__(self):
        return f"{self.buyer} asks for {self.item}"