from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q

from app.models import Role


def get_grouped_permissions():
    """
    Returns permissions grouped by app label and model name for easy UI rendering.
    """
    permissions = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'name'
    )
    
    grouped = {}
    for perm in permissions:
        if perm.content_type:
            app_name = perm.content_type.app_label.title()
            model_name = perm.content_type.name.title()
            group_name = f"{app_name} › {model_name}"
        else:
            group_name = "General Permissions"

        if group_name not in grouped:
            grouped[group_name] = {
                'id': group_name.lower().replace(' ', '_').replace('›', '_'),
                'title': group_name,
                'perms': []
            }
        grouped[group_name]['perms'].append(perm)

    return list(grouped.values())


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def roles_list_view(request):
    """
    List all dynamic roles with user counts and permission statistics.
    """
    if not (request.user.is_superuser or request.user.has_perm('app.view_role') or request.user.has_perm('app.change_role') or request.user.has_perm('app.add_role')):
        raise PermissionDenied("You do not have permission to view roles.")

    query = request.GET.get('q', '').strip()
    roles = Role.objects.annotate(
        user_count=Count('profiles', distinct=True),
        perm_count=Count('permissions', distinct=True)
    ).all().order_by('name')

    if query:
        roles = roles.filter(Q(name__icontains=query) | Q(description__icontains=query))

    context = {
        'roles': roles,
        'query': query,
        'total_roles': Role.objects.count(),
        'total_users': User.objects.count(),
        'total_permissions': Permission.objects.count(),
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/roles/index.html', context)


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def role_add_view(request):
    """
    Create a new dynamic role with specific permissions.
    """
    if not (request.user.is_superuser or request.user.has_perm('app.add_role')):
        raise PermissionDenied("You do not have permission to add roles.")

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        perm_ids = request.POST.getlist('permissions')

        errors = []
        if not name:
            errors.append("Role name is required.")
        elif Role.objects.filter(name__iexact=name).exists():
            errors.append(f'A role named "{name}" already exists.')

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            try:
                role = Role.objects.create(name=name, description=description)
                
                # Assign selected permissions
                if perm_ids:
                    permissions = Permission.objects.filter(id__in=perm_ids)
                    role.permissions.set(permissions)
                
                # Synchronize to Django Group
                role.sync_to_group()

                messages.success(request, f'Role "{role.name}" was created successfully with {role.permissions.count()} permissions!')
                
                if request.POST.get('_addanother'):
                    return redirect('custom_admin_role_add')
                return redirect('custom_admin_roles')
            except Exception as e:
                messages.error(request, f"Error creating role: {str(e)}")

    context = {
        'grouped_permissions': get_grouped_permissions(),
        'selected_perm_ids': [int(p) for p in request.POST.getlist('permissions')] if request.method == 'POST' else [],
        'is_edit': False,
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/roles/form.html', context)


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def role_edit_view(request, role_id):
    """
    Edit an existing dynamic role and synchronize its permissions across all assigned users.
    """
    if not (request.user.is_superuser or request.user.has_perm('app.change_role')):
        raise PermissionDenied("You do not have permission to edit roles.")

    role = get_object_or_404(Role, pk=role_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        perm_ids = request.POST.getlist('permissions')

        errors = []
        if not name:
            errors.append("Role name is required.")
        elif Role.objects.filter(name__iexact=name).exclude(pk=role.pk).exists():
            errors.append(f'Another role named "{name}" already exists.')

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            try:
                role.name = name
                role.description = description
                role.save()

                # Update permissions
                permissions = Permission.objects.filter(id__in=perm_ids)
                role.permissions.set(permissions)
                
                # Sync with group
                role.sync_to_group()

                messages.success(request, f'Role "{role.name}" updated successfully!')
                return redirect('custom_admin_roles')
            except Exception as e:
                messages.error(request, f"Error updating role: {str(e)}")

    selected_perm_ids = list(role.permissions.values_list('id', flat=True))

    context = {
        'role': role,
        'grouped_permissions': get_grouped_permissions(),
        'selected_perm_ids': selected_perm_ids,
        'is_edit': True,
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/roles/form.html', context)


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def role_delete_view(request, role_id):
    """
    Safely delete a role and detach it from all assigned users.
    """
    if not (request.user.is_superuser or request.user.has_perm('app.delete_role')):
        raise PermissionDenied("You do not have permission to delete roles.")

    role = get_object_or_404(Role, pk=role_id)
    
    if request.method == 'POST':
        role_name = role.name
        # Delete associated group if any
        if role.group:
            role.group.delete()
        role.delete()
        messages.success(request, f'Role "{role_name}" was deleted successfully.')
        return redirect('custom_admin_roles')

    context = {
        'role': role,
        'assigned_users': role.profiles.select_related('user').all(),
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/roles/delete_confirm.html', context)
