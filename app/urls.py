from django.urls import path
from app.controllers import (
    custom_admin_login_view,
    admin_logout_view,
    profile_view,
    users_list_view,
    user_add_view,
    settings_view,
)

urlpatterns = [
    path('login/', custom_admin_login_view, name='custom_admin_login'),
    path('logout/', admin_logout_view, name='custom_admin_logout'),
    path('profile/', profile_view, name='custom_admin_profile'),
    path('users/add/', user_add_view, name='custom_admin_user_add'),
    path('auth/user/add/', user_add_view, name='custom_admin_auth_user_add'),
    path('users/', users_list_view, name='custom_admin_users'),
    path('settings/', settings_view, name='custom_admin_settings'),
]
