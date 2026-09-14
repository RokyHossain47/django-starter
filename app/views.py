import sys
import django
from django.contrib import admin
from django.contrib.auth import logout
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Q


def setup_admin_customizations():
    """
    Configures admin branding and wraps admin.site.index
    to provide rich dashboard analytics context.
    """
    admin.site.site_header = "Master Admin Panel"
    admin.site.site_title = "Admin Dashboard"
    admin.site.index_title = "System Overview & Analytics"
    admin.site.index_template = "admin/dashboard.html"

    original_admin_index = admin.site.index

    def custom_admin_index(request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        try:
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            staff_users = User.objects.filter(is_staff=True).count()
            superusers_count = User.objects.filter(is_superuser=True).count()
            total_groups = Group.objects.count()
            recent_actions = LogEntry.objects.select_related('content_type', 'user').order_by('-action_time')[:10]
            recent_users = User.objects.order_by('-date_joined')[:6]
        except Exception:
            total_users = 0
            active_users = 0
            staff_users = 0
            superusers_count = 0
            total_groups = 0
            recent_actions = []
            recent_users = []

        extra_context.update({
            'total_users': total_users,
            'active_users': active_users,
            'staff_users': staff_users,
            'superusers_count': superusers_count,
            'total_groups': total_groups,
            'recent_actions': recent_actions,
            'recent_users': recent_users,
            'django_version': django.get_version(),
            'python_version': sys.version.split(' ')[0],
            'server_time': timezone.now(),
        })
        return original_admin_index(request, extra_context=extra_context)

    admin.site.index = custom_admin_index


@staff_member_required(login_url='/admin/login/')
def users_list_view(request):
    """
    Custom Users Management view loaded from templates/admin/users/index.html
    """
    query = request.GET.get('q', '').strip()
    staff_filter = request.GET.get('is_staff')
    superuser_filter = request.GET.get('is_superuser')
    active_filter = request.GET.get('is_active')

    users = User.objects.all().order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    if staff_filter in ['0', '1']:
        users = users.filter(is_staff=(staff_filter == '1'))

    if superuser_filter in ['0', '1']:
        users = users.filter(is_superuser=(superuser_filter == '1'))

    if active_filter in ['0', '1']:
        users = users.filter(is_active=(active_filter == '1'))

    context = {
        'users': users,
        'query': query,
        'current_staff_filter': staff_filter,
        'current_superuser_filter': superuser_filter,
        'current_active_filter': active_filter,
        'total_users': User.objects.count(),
        'total_groups': Group.objects.count(),
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/users/index.html', context)


@staff_member_required(login_url='/admin/login/')
def settings_view(request):
    """
    Custom Settings view loaded from templates/admin/settings/index.html
    """
    context = {
        'django_version': django.get_version(),
        'python_version': sys.version.split(' ')[0],
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
        'total_users': User.objects.count(),
        'total_groups': Group.objects.count(),
    }
    return render(request, 'admin/settings/index.html', context)


def admin_logout_view(request):
    """
    Handles logging out the user and safely redirecting to /admin/login/
    """
    logout(request)
    return redirect('/admin/login/')
