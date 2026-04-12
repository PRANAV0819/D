from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from apps.chat.models import Message, ChatRoom
from apps.connections.models import Connection
from apps.mentorship.models import MentorshipRequest
from apps.projects.models import ProjectMember
from apps.notifications.models import Notification

@receiver(post_save, sender=Message)
def message_notification(sender, instance, created, **kwargs):
    if created:
        room = instance.room
        # We only notify for DM rooms to avoid spamming groups, or we can do both. 
        # Here we do both but handle them accordingly.
        if room.room_type == ChatRoom.RoomType.DM:
            other = room.get_other_member(instance.sender)
            if other:
                Notification.send(
                    recipient=other,
                    notif_type=Notification.NotifType.MESSAGE,
                    title=f"New message from {instance.sender.get_full_name()}",
                    message=f"{instance.content[:50]}..." if len(instance.content) > 50 else instance.content,
                    link=reverse('chat:room', args=[room.pk])
                )
        elif room.room_type == ChatRoom.RoomType.GROUP:
            for member in room.members.exclude(pk=instance.sender.pk):
                Notification.send(
                    recipient=member,
                    notif_type=Notification.NotifType.MESSAGE,
                    title=f"New message in {room.name}",
                    message=f"{instance.sender.first_name}: {instance.content[:30]}",
                    link=reverse('chat:room', args=[room.pk])
                )

@receiver(post_save, sender=Connection)
def connection_notification(sender, instance, created, **kwargs):
    if created and instance.status == Connection.Status.PENDING:
        Notification.send(
            recipient=instance.receiver,
            notif_type=Notification.NotifType.CONNECTION,
            title="New Connection Request",
            message=f"{instance.sender.get_full_name()} wants to connect with you.",
            link=reverse('connections:network')
        )

@receiver(post_save, sender=MentorshipRequest)
def mentorship_notification(sender, instance, created, **kwargs):
    if created and instance.status == MentorshipRequest.Status.PENDING:
        Notification.send(
            recipient=instance.mentor,
            notif_type=Notification.NotifType.MENTORSHIP,
            title="New Mentorship Request",
            message=f"{instance.mentee.get_full_name()} has requested you as a mentor.",
            link=reverse('mentorship:my')
        )

@receiver(post_save, sender=ProjectMember)
def project_member_notification(sender, instance, created, **kwargs):
    # Only notify if they are actively requesting to join and not yet approved.
    # We do not notify when the owner auto-creates their own membership (which has is_approved=True).
    if created and not instance.is_approved:
        if instance.user != instance.project.owner:
            Notification.send(
                recipient=instance.project.owner,
                notif_type=Notification.NotifType.PROJECT,
                title="Project Join Request",
                message=f"{instance.user.get_full_name()} wants to join '{instance.project.title}'.",
                link=reverse('projects:detail', args=[instance.project.pk])
            )
