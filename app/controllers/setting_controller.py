import os
import time
import sys
import django
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect

from app.models import Setting


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def settings_view(request):
    """
    Custom Settings view loaded from templates/admin/settings/index.html
    Handles displaying and updating application, branding, and system configurations.
    """
    if not (request.user.is_superuser or request.user.has_perm('app.view_setting') or request.user.has_perm('app.change_setting')):
        raise PermissionDenied("You do not have permission to view system settings.")

    if request.method == 'POST':
        if not (request.user.is_superuser or request.user.has_perm('app.change_setting')):
            raise PermissionDenied("You do not have permission to change system settings.")
        
        action = request.POST.get('action')
        
        if action == 'save_settings':
            # Handle text settings
            site_title = request.POST.get('site_header_title', '').strip()
            if site_title:
                Setting.set_value('site_header_title', site_title, description='Site Header & Branding Title', is_public=True)

            admin_email = request.POST.get('admin_email', '').strip()
            if admin_email:
                Setting.set_value('admin_email', admin_email, description='Administrator Contact Email', is_public=False)

            # Handle Logo Removal
            if request.POST.get('remove_site_logo') == '1':
                Setting.set_value('site_logo', '', description='Site Branding Logo', is_public=True)

            # Handle Logo Upload
            if 'site_logo' in request.FILES:
                logo_file = request.FILES['site_logo']
                ext = os.path.splitext(logo_file.name)[1].lower()
                logo_name = f"settings/logo_{int(time.time())}{ext}"
                saved_path = default_storage.save(logo_name, logo_file)
                Setting.set_value('site_logo', saved_path, description='Site Branding Logo', is_public=True)

            # Handle Favicon Removal
            if request.POST.get('remove_site_favicon') == '1':
                Setting.set_value('site_favicon', '', description='Site Favicon Icon', is_public=True)

            # Handle Favicon Upload
            if 'site_favicon' in request.FILES:
                favicon_file = request.FILES['site_favicon']
                ext = os.path.splitext(favicon_file.name)[1].lower()
                favicon_name = f"settings/favicon_{int(time.time())}{ext}"
                saved_path = default_storage.save(favicon_name, favicon_file)
                Setting.set_value('site_favicon', saved_path, description='Site Favicon Icon', is_public=True)

            messages.success(request, 'Settings & branding updated successfully!')
            return redirect('custom_admin_settings')

    settings_list = Setting.objects.all()

    context = {
        'django_version': django.get_version(),
        'python_version': sys.version.split(' ')[0],
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
        'total_users': User.objects.count(),
        'total_groups': Group.objects.count(),
        'settings_list': settings_list,
    }
    return render(request, 'admin/settings/index.html', context)

