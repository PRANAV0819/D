from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('',               views.event_list_view,    name='list'),
    path('create/',        views.create_event_view,  name='create'),
    path('<int:pk>/',      views.event_detail_view,  name='detail'),
    path('<int:pk>/register/', views.register_event_view, name='register'),
]