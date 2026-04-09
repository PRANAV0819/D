from django.db import models
from django.conf import settings
from django.utils import timezone


class ChatRoom(models.Model):

    class RoomType(models.TextChoices):
        DM    = 'dm',    'Direct Message'
        GROUP = 'group', 'Group Chat'

    room_type  = models.CharField(
        max_length=10, choices=RoomType.choices, default=RoomType.DM
    )
    name       = models.CharField(max_length=200, blank=True)  # group chats only
    members    = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='RoomMember',
        related_name='chat_rooms',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_rooms',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.room_type == self.RoomType.DM:
            return f'DM #{self.pk}'
        return self.name or f'Group #{self.pk}'

    def get_other_member(self, user):
        """For DMs: returns the other participant."""
        return self.members.exclude(pk=user.pk).first()

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    @classmethod
    def get_or_create_dm(cls, user1, user2):
        """
        Find an existing DM between exactly these two users,
        or create a new one. Returns (room, created).
        """
        from django.db.models import Count
        existing = (
            cls.objects
            .filter(room_type=cls.RoomType.DM, members=user1)
            .filter(members=user2)
            .annotate(cnt=Count('members'))
            .filter(cnt=2)
            .first()
        )
        if existing:
            return existing, False

        room = cls.objects.create(room_type=cls.RoomType.DM, created_by=user1)
        RoomMember.objects.create(room=room, user=user1)
        RoomMember.objects.create(room=room, user=user2)
        return room, True


class RoomMember(models.Model):
    room      = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name='room_members'
    )
    user      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='room_memberships',
    )
    last_read = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f'{self.user.email} in Room #{self.room_id}'

    def unread_count(self):
        qs = self.room.messages.exclude(sender=self.user)
        if self.last_read:
            qs = qs.filter(created_at__gt=self.last_read)
        return qs.count()


class Message(models.Model):
    room       = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name='messages'
    )
    sender     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    content    = models.TextField(max_length=5000, blank=True)
    image      = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    is_seen    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.email}: {self.content[:50]}'

    def timestamp(self):
        return self.created_at.strftime('%H:%M')