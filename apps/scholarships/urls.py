from django.urls import path
from . import views

app_name = 'scholarships'

urlpatterns = [
    path('',            views.scholarship_list_view,   name='list'),
    path('post/',       views.post_scholarship_view,   name='post'),
    path('<int:pk>/',   views.scholarship_detail_view, name='detail'),
]