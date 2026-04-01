from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('',                    views.inbox_view,     name='inbox'),
    path('room/<int:room_id>/', views.room_view,      name='room'),
    path('dm/<int:user_id>/',   views.create_dm_view, name='create_dm'),
]