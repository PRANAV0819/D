from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# ─────────────────────────────────────────────
# Lost & Found Models
# ─────────────────────────────────────────────

class Item(models.Model):
    """A single lost or found item report."""

    class ItemType(models.TextChoices):
        LOST = 'lost', _('Lost')
        FOUND = 'found', _('Found')

    class Category(models.TextChoices):
        ID_CARD = 'id_card', _('ID Card')
        BOOK = 'book', _('Book')
        BOTTLE = 'bottle', _('Bottle')
        ELECTRONICS = 'electronics', _('Electronics')
        BAG = 'bag', _('Bag')
        KEYS = 'keys', _('Keys')
        WALLET = 'wallet', _('Wallet')
        CLOTHING = 'clothing', _('Clothing')
        OTHER = 'other', _('Other')

    class Status(models.TextChoices):
        OPEN = 'open', _('Open')
        CLAIMED = 'claimed', _('Claimed')
        RESOLVED = 'resolved', _('Resolved')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lost_found_items'
    )
    item_type = models.CharField(
        max_length=10, 
        choices=ItemType.choices,
        db_index=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=20, 
        choices=Category.choices, 
        default=Category.OTHER,
        db_index=True
    )
    location = models.CharField(max_length=200)
    date = models.DateField(help_text="Date the item was lost or found")
    image = models.ImageField(upload_to='lost_found/', blank=True, null=True)
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.OPEN,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_item_type_display()}] {self.title}'

    @property
    def opposite_type(self):
        return self.ItemType.FOUND if self.item_type == self.ItemType.LOST else self.ItemType.LOST


class ClaimRequest(models.Model):
    """A claimant asserts that a Found item belongs to them."""

    class ClaimStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')

    item = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE, 
        related_name='claims'
    )
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='my_claims'
    )
    message = models.TextField(help_text="Describe why you believe this item is yours.")
    status = models.CharField(
        max_length=20, 
        choices=ClaimStatus.choices, 
        default=ClaimStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('item', 'claimant')

    def __str__(self):
        return f'Claim by {self.claimant.email} on {self.item.title}'