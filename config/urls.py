from django.contrib import admin
from django.urls import path
from app.views import setup_admin_customizations, admin_logout_view, users_list_view, settings_view

# Initialize Admin site custom index and settings
setup_admin_customizations()

urlpatterns = [
    path('admin/logout/', admin_logout_view, name='custom_admin_logout'),
    path('admin/users/', users_list_view, name='custom_admin_users'),
    path('admin/settings/', settings_view, name='custom_admin_settings'),
    path('admin/', admin.site.urls),
]
