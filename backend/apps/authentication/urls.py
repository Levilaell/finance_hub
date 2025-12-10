from django.urls import path
from .views import register_view, login_view, RefreshView, profile_view, user_settings_view

app_name = 'authentication'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('refresh/', RefreshView.as_view(), name='refresh'),  # ← Class-based
    path('profile/', profile_view, name='profile'),
    path('settings/', user_settings_view, name='settings'),
]