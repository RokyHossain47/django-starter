from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Group, Permission
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404

from app.models import Role


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def roles_list_view(request):
    """
    List all roles / groups with permission counts.
    """
    roles = Role.objects.prefetch_related('permissions').all()
    groups = Group.objects.prefetch_related('permissions').all()

    context = {
        'roles': roles,
        'groups': groups,
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/roles/index.html' if False else 'admin/dashboard.html', context)
