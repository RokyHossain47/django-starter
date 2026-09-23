from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from app.models import Profile, Role


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def profile_view(request):
    """
    Custom Super Admin Profile view to update username, first/last name, email, avatar, and password.
    """
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_info':
            username = request.POST.get('username', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()

            if not username:
                messages.error(request, 'Username cannot be empty.')
            elif User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, f'Username "{username}" is already taken by another user.')
            else:
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save()

                if 'avatar' in request.FILES:
                    profile.avatar = request.FILES['avatar']
                    profile.save()
                elif request.POST.get('remove_avatar') == '1':
                    if profile.avatar:
                        profile.avatar.delete(save=False)
                        profile.avatar = None
                        profile.save()

                messages.success(request, 'Profile details updated successfully!')
                return redirect('custom_admin_profile')

        elif action == 'update_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not user.check_password(current_password):
                messages.error(request, 'Your current password was entered incorrectly.')
            elif not new_password:
                messages.error(request, 'New password cannot be empty.')
            elif len(new_password) < 6:
                messages.error(request, 'New password must be at least 6 characters long.')
            elif new_password != confirm_password:
                messages.error(request, 'The two password fields did not match.')
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was changed successfully!')
                return redirect('custom_admin_profile')

    context = {
        'user': user,
        'profile': profile,
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/profile/index.html', context)


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def user_add_view(request):
    """
    Rich User Creation view supporting mandatory email, role selection,
    optional company name, optional phone, optional profile image, and auto-generated password.
    """
    if not (request.user.is_superuser or request.user.has_perm('auth.add_user')):
        raise PermissionDenied("You do not have permission to add users.")

    roles = Role.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        company_name = request.POST.get('company_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role_id = request.POST.get('role_id', '').strip()
        
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        is_active = request.POST.get('is_active') == 'on'

        # If user has a role assigned, automatically grant staff status so they can log into admin
        if role_id:
            is_staff = True

        errors = []
        if not username:
            errors.append("Username is required.")
        elif User.objects.filter(username=username).exists():
            errors.append(f'Username "{username}" is already taken.')

        if not email:
            errors.append("Email address is mandatory.")
        elif '@' not in email or '.' not in email:
            errors.append("Please enter a valid email address.")

        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                    is_active=is_active
                )
                
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.company_name = company_name
                profile.phone = phone
                if 'avatar' in request.FILES:
                    profile.avatar = request.FILES['avatar']
                
                # Assign Role if selected
                if role_id:
                    try:
                        role = Role.objects.get(id=role_id)
                        profile.role = role
                    except Role.DoesNotExist:
                        pass
                profile.save()

                messages.success(request, f'User "{user.username}" was created successfully!')
                
                if request.POST.get('_addanother'):
                    return redirect('custom_admin_user_add')
                return redirect('custom_admin_users')
            except Exception as e:
                messages.error(request, f"Error creating user: {str(e)}")

    context = {
        'roles': roles,
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/users/add.html', context)


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def users_list_view(request):
    """
    Custom Users Management view with role filtering and role badges.
    """
    if not (request.user.is_superuser or request.user.has_perm('auth.view_user') or request.user.has_perm('auth.change_user')):
        raise PermissionDenied("You do not have permission to view users.")

    query = request.GET.get('q', '').strip()
    staff_filter = request.GET.get('is_staff')
    superuser_filter = request.GET.get('is_superuser')
    active_filter = request.GET.get('is_active')
    role_filter = request.GET.get('role')

    users = User.objects.select_related('profile', 'profile__role').all().order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__company_name__icontains=query) |
            Q(profile__phone__icontains=query) |
            Q(profile__role__name__icontains=query)
        )

    if staff_filter in ['0', '1']:
        users = users.filter(is_staff=(staff_filter == '1'))

    if superuser_filter in ['0', '1']:
        users = users.filter(is_superuser=(superuser_filter == '1'))

    if active_filter in ['0', '1']:
        users = users.filter(is_active=(active_filter == '1'))

    if role_filter:
        users = users.filter(profile__role_id=role_filter)

    roles = Role.objects.all()

    context = {
        'users': users,
        'roles': roles,
        'query': query,
        'current_staff_filter': staff_filter,
        'current_superuser_filter': superuser_filter,
        'current_active_filter': active_filter,
        'current_role_filter': role_filter,
        'total_users': User.objects.count(),
        'total_groups': Group.objects.count(),
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/users/index.html', context)


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def user_edit_view(request, user_id):
    """
    Edit an existing user, assign roles, update profile, and optionally reset password.
    """
    if not (request.user.is_superuser or request.user.has_perm('auth.change_user')):
        raise PermissionDenied("You do not have permission to edit users.")

    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = Profile.objects.get_or_create(user=target_user)
    roles = Role.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        company_name = request.POST.get('company_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role_id = request.POST.get('role_id', '').strip()

        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        is_active = request.POST.get('is_active') == 'on'

        if role_id:
            is_staff = True

        errors = []
        if not username:
            errors.append("Username is required.")
        elif User.objects.filter(username=username).exclude(pk=target_user.pk).exists():
            errors.append(f'Username "{username}" is already taken.')

        if not email:
            errors.append("Email address is mandatory.")
        elif '@' not in email or '.' not in email:
            errors.append("Please enter a valid email address.")

        if password and len(password) < 6:
            errors.append("New password must be at least 6 characters long.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            try:
                target_user.username = username
                target_user.email = email
                target_user.first_name = first_name
                target_user.last_name = last_name
                target_user.is_staff = is_staff
                target_user.is_superuser = is_superuser
                target_user.is_active = is_active

                if password:
                    target_user.set_password(password)

                target_user.save()

                profile.company_name = company_name
                profile.phone = phone
                if 'avatar' in request.FILES:
                    profile.avatar = request.FILES['avatar']
                elif request.POST.get('remove_avatar') == '1' and profile.avatar:
                    profile.avatar.delete(save=False)
                    profile.avatar = None

                if role_id:
                    try:
                        role = Role.objects.get(id=role_id)
                        profile.role = role
                    except Role.DoesNotExist:
                        profile.role = None
                else:
                    profile.role = None

                profile.save()

                messages.success(request, f'User "{target_user.username}" updated successfully!')
                return redirect('custom_admin_users')
            except Exception as e:
                messages.error(request, f"Error updating user: {str(e)}")

    context = {
        'target_user': target_user,
        'profile': profile,
        'roles': roles,
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/users/edit.html', context)


@staff_member_required(login_url='/admin/login/', redirect_field_name=None)
def user_delete_view(request, user_id):
    """
    Safely delete a user account.
    """
    if not (request.user.is_superuser or request.user.has_perm('auth.delete_user')):
        raise PermissionDenied("You do not have permission to delete users.")

    target_user = get_object_or_404(User, pk=user_id)

    if request.user.pk == target_user.pk:
        messages.error(request, "You cannot delete your own account.")
        return redirect('custom_admin_users')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f'User "{username}" was deleted successfully.')
        return redirect('custom_admin_users')

    context = {
        'target_user': target_user,
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }
    return render(request, 'admin/users/delete_confirm.html', context)

