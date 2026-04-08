from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('',                             views.inbox_view,        name='inbox'),
    path('room/<int:room_id>/',          views.room_view,         name='room'),
    path('room/<int:room_id>/delete/',   views.delete_room_view,  name='delete_room'),
    path('dm/<int:user_id>/',            views.create_dm_view,    name='create_dm'),
    # AJAX fallback: poll new messages
    path('api/messages/<int:room_id>/',  views.poll_messages_view, name='poll_messages'),
    # AJAX fallback: send a message (POST only)
    path('api/send/<int:room_id>/',      views.send_message_view,  name='send_message'),
]