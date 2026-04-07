from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('',                             views.inbox_view,        name='inbox'),
    path('room/<int:room_id>/',          views.room_view,         name='room'),
    path('dm/<int:user_id>/',            views.create_dm_view,    name='create_dm'),
    # AJAX fallback endpoint: polls new messages without WebSocket
    path('api/messages/<int:room_id>/',  views.poll_messages_view, name='poll_messages'),
]