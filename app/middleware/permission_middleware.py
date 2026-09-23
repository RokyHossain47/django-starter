import re
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.contrib.auth import logout


class AdminPermissionMiddleware:
    """
    Middleware that intercepts all admin routes (/admin/...) and verifies
    granular permissions for staff users before passing the request forward.
    Superusers have full access to all routes.
    """

    EXEMPT_PATHS = [
        '/admin/login/',
        '/admin/logout/',
        '/admin/password_reset/',
        '/admin/password_reset/done/',
        '/admin/reset/',
        '/admin/jsi18n/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1. Non-admin routes are ignored
        if not path.startswith('/admin/'):
            return self.get_response(request)

        # 2. Public auth routes under /admin/ are allowed
        for exempt in self.EXEMPT_PATHS:
            if path.startswith(exempt):
                return self.get_response(request)

        # 3. Check authentication & staff status
        if not request.user.is_authenticated:
            return redirect('/admin/login/')

        if not request.user.is_staff:
            logout(request)
            return redirect('/admin/login/')

        # 4. Superuser gets full unrestricted access
        if request.user.is_superuser:
            return self.get_response(request)

        # 5. Granular permission checking for regular staff users
        # Dashboard, self-profile, password change are accessible to all staff
        if path in ['/admin/', '/admin/profile/', '/admin/password_change/', '/admin/password_change/done/']:
            return self.get_response(request)

        # Custom Users routes
        if path.startswith('/admin/users/add/') or path.startswith('/admin/auth/user/add/'):
            if not request.user.has_perm('auth.add_user'):
                return self._permission_denied(request, "auth.add_user", "Add User")
            return self.get_response(request)

        if path.startswith('/admin/users/') or path.startswith('/admin/auth/user/'):
            if not (request.user.has_perm('auth.view_user') or request.user.has_perm('auth.change_user')):
                return self._permission_denied(request, "auth.view_user", "View Users")
            return self.get_response(request)

        # Custom Roles routes
        if path.startswith('/admin/roles/add/'):
            if not request.user.has_perm('app.add_role'):
                return self._permission_denied(request, "app.add_role", "Create Role")
            return self.get_response(request)

        if re.search(r'^/admin/roles/\d+/edit/?$', path):
            if not request.user.has_perm('app.change_role'):
                return self._permission_denied(request, "app.change_role", "Edit Role")
            return self.get_response(request)

        if re.search(r'^/admin/roles/\d+/delete/?$', path):
            if not request.user.has_perm('app.delete_role'):
                return self._permission_denied(request, "app.delete_role", "Delete Role")
            return self.get_response(request)

        if path.startswith('/admin/roles/'):
            if not (request.user.has_perm('app.view_role') or request.user.has_perm('app.change_role') or request.user.has_perm('app.add_role')):
                return self._permission_denied(request, "app.view_role", "View Roles")
            return self.get_response(request)

        # Settings routes (Settings is admin-only, unless specific permission is granted)
        if path.startswith('/admin/settings/') or path.startswith('/admin/app/setting/'):
            if not (request.user.has_perm('app.view_setting') or request.user.has_perm('app.change_setting')):
                return self._permission_denied(request, "app.view_setting", "System Settings")
            return self.get_response(request)

        # Dynamic Django Model routes (/admin/<app_label>/<model_name>/...)
        match_add = re.match(r'^/admin/(?P<app_label>[\w-]+)/(?P<model_name>[\w-]+)/add/?', path)
        if match_add:
            app_label = match_add.group('app_label')
            model_name = match_add.group('model_name')
            perm_code = f"{app_label}.add_{model_name}"
            if not request.user.has_perm(perm_code):
                return self._permission_denied(request, perm_code, f"Add {model_name.title()}")
            return self.get_response(request)

        match_change = re.match(r'^/admin/(?P<app_label>[\w-]+)/(?P<model_name>[\w-]+)/(?P<id>[\w-]+)/change/?', path)
        if match_change:
            app_label = match_change.group('app_label')
            model_name = match_change.group('model_name')
            perm_code = f"{app_label}.change_{model_name}"
            if not request.user.has_perm(perm_code):
                return self._permission_denied(request, perm_code, f"Change {model_name.title()}")
            return self.get_response(request)

        match_delete = re.match(r'^/admin/(?P<app_label>[\w-]+)/(?P<model_name>[\w-]+)/(?P<id>[\w-]+)/delete/?', path)
        if match_delete:
            app_label = match_delete.group('app_label')
            model_name = match_delete.group('model_name')
            perm_code = f"{app_label}.delete_{model_name}"
            if not request.user.has_perm(perm_code):
                return self._permission_denied(request, perm_code, f"Delete {model_name.title()}")
            return self.get_response(request)

        match_list = re.match(r'^/admin/(?P<app_label>[\w-]+)/(?P<model_name>[\w-]+)/?$', path)
        if match_list:
            app_label = match_list.group('app_label')
            model_name = match_list.group('model_name')
            view_perm = f"{app_label}.view_{model_name}"
            change_perm = f"{app_label}.change_{model_name}"
            if not (request.user.has_perm(view_perm) or request.user.has_perm(change_perm)):
                return self._permission_denied(request, view_perm, f"View {model_name.title()}")
            return self.get_response(request)

        return self.get_response(request)

    def _permission_denied(self, request, permission_code, action_name):
        context = {
            'permission_code': permission_code,
            'action_name': action_name,
            'user': request.user,
        }
        return render(request, 'admin/errors/403.html', context, status=403)
