from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('',                      views.job_list_view,        name='list'),
    path('post/',                 views.post_job_view,        name='post'),
    path('mine/',                 views.my_jobs_view,         name='my_jobs'),
    path('<int:pk>/',             views.job_detail_view,      name='detail'),
    path('<int:pk>/apply/',       views.apply_job_view,       name='apply'),
    path('<int:pk>/toggle/',      views.toggle_job_status_view, name='toggle'),
]