from django.db import models
from django.conf import settings


class Connection(models.Model):

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'

    sender   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_requests',
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_requests',
    )
    status     = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender} → {self.receiver} [{self.status}]'

    @classmethod
    def get_status_between(cls, user_a, user_b):
        """
        Returns the Connection object between two users, or None.
        Checks both directions.
        """
        return cls.objects.filter(
            models.Q(sender=user_a, receiver=user_b) |
            models.Q(sender=user_b, receiver=user_a)
        ).first()

    @classmethod
    def accepted_ids_for(cls, user):
        """Return a set of user IDs connected to `user`."""
        qs = cls.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user),
            status=cls.Status.ACCEPTED,
        ).values_list('sender_id', 'receiver_id')
        ids = set()
        for s, r in qs:
            ids.add(s if s != user.pk else r)
        return ids