from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('',                              views.project_list_view,       name='list'),
    path('create/',                       views.create_project_view,     name='create'),
    path('mine/',                         views.my_projects_view,        name='mine'),
    path('<int:pk>/',                     views.project_detail_view,     name='detail'),
    path('<int:pk>/join/',                views.join_project_view,       name='join'),
    path('<int:pk>/approve/<int:member_id>/', views.approve_member_view, name='approve'),
    path('<int:pk>/task/add/',            views.add_task_view,           name='add_task'),
    path('task/<int:task_id>/status/',    views.update_task_status_view, name='task_status'),
]