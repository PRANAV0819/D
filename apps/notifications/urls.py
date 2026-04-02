from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',                     views.notification_list_view, name='list'),
    path('unread-count/',        views.unread_count_view,      name='unread_count'),
    path('<int:pk>/read/',       views.mark_read_view,         name='mark_read'),
]