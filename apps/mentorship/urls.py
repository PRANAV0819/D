from django.urls import path
from . import views

app_name = 'mentorship'

urlpatterns = [
    path('',                               views.mentor_list_view,    name='list'),
    path('become/',                        views.become_mentor_view,  name='become'),
    path('my/',                            views.my_mentorship_view,  name='my'),
    path('mentor/<int:user_id>/',          views.mentor_detail_view,  name='detail'),
    path('mentor/<int:user_id>/request/',  views.send_request_view,   name='send_request'),
    path('request/<int:req_id>/<str:action>/', views.handle_request_view, name='handle'),
    path('session/<int:req_id>/book/',     views.book_session_view,   name='book'),
]