import sys
import django
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry
from django.utils import timezone


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

        is_superuser = request.user.is_superuser
        user_role = getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None

        if is_superuser:
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
                'is_admin_dashboard': True,
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
        else:
            try:
                # Regular staff user: only show their own relevant data and actions
                my_recent_actions = LogEntry.objects.filter(user=request.user).select_related('content_type').order_by('-action_time')[:10]
                my_permissions = sorted(list(request.user.get_all_permissions()))
            except Exception:
                my_recent_actions = []
                my_permissions = []

            extra_context.update({
                'is_admin_dashboard': False,
                'my_role': user_role,
                'my_permissions': my_permissions,
                'my_permissions_count': len(my_permissions),
                'recent_actions': my_recent_actions,
                'server_time': timezone.now(),
            })

        return original_admin_index(request, extra_context=extra_context)

    admin.site.index = custom_admin_index

