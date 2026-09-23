import sys
import django
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect

from app.models import Setting


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def settings_view(request):
    """
    Custom Settings view loaded from templates/admin/settings/index.html
    Handles displaying and updating application and system configurations.
    """
    if not (request.user.is_superuser or request.user.has_perm('app.view_setting') or request.user.has_perm('app.change_setting')):
        raise PermissionDenied("You do not have permission to view system settings.")

    if request.method == 'POST':
        if not (request.user.is_superuser or request.user.has_perm('app.change_setting')):
            raise PermissionDenied("You do not have permission to change system settings.")
        
        action = request.POST.get('action')
        
        if action == 'save_settings':
            # Example dynamic setting update
            for key, val in request.POST.items():
                if key not in ['csrfmiddlewaretoken', 'action']:
                    Setting.set_value(key=key, value=val)
            messages.success(request, 'System settings updated successfully!')
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
