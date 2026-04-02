from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('',              views.marketplace_list_view,   name='list'),
    path('post/',         views.post_item_view,          name='post'),
    path('mine/',         views.my_items_view,           name='my_items'),
    path('<int:pk>/',     views.marketplace_detail_view, name='detail'),
    path('<int:pk>/sold/', views.mark_sold_view,         name='sold'),
]