from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('room/<int:room_id>/', views.room_view, name='room'),
    path('start/<int:user_id>/', views.start_chat_view, name='start_chat'),
    path('search/', views.search_users_view, name='search'),
    path('upload/', views.upload_file_view, name='upload_file'),
]
