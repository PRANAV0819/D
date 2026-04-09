from django.urls import path
from . import views

app_name = 'lost_found'

urlpatterns = [
    path('',               views.lf_list_view,    name='list'),
    path('post/',          views.lf_post_view,    name='post'),
    path('<int:pk>/',      views.lf_detail_view,  name='detail'),
    path('<int:pk>/resolve/', views.lf_resolve_view, name='resolve'),
    path('<int:pk>/delete/', views.lf_delete_view, name='delete'),
]