from django.urls import path
from . import views

app_name = 'connections'

urlpatterns = [
    path('',                                  views.network_view,          name='network'),
    path('search/',                           views.people_search_view,    name='search'),
    path('send/<int:user_id>/',               views.send_request_view,     name='send_request'),
    path('accept/<int:connection_id>/',       views.accept_request_view,   name='accept'),
    path('reject/<int:connection_id>/',       views.reject_request_view,   name='reject'),
    path('remove/<int:user_id>/',             views.remove_connection_view,name='remove'),
    path('status/<int:user_id>/',             views.connection_status_view,name='status'),
]