from django.urls import path
from . import views

app_name = 'lost_found'

urlpatterns = [
    path('',                  views.item_list,   name='list'),
    path('post/',             views.item_create, name='create'),
    path('item/<int:pk>/',    views.item_detail, name='detail'),
    path('item/<int:pk>/claim/', views.claim_item, name='claim_item'),
    path('claim/<int:pk>/<str:action>/', views.manage_claim, name='manage_claim'),
]