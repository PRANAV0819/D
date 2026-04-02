from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('',                    views.resource_list_view,    name='list'),
    path('upload/',             views.upload_resource_view,  name='upload'),
    path('<int:pk>/download/',  views.download_resource_view,name='download'),
]