from django.contrib import admin
from django.contrib.auth import logout, authenticate, login as auth_login
from django.shortcuts import render, redirect


def custom_admin_login_view(request):
    """
    Clean admin login view that avoids ugly '?next=/admin/' query params in URLs.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('/admin/')

    # Clean URL redirect if accessed with ?next=/admin/ or ?next=
    if request.method == 'GET' and ('next' in request.GET and (request.GET.get('next') in ['/admin/', '/admin', ''])):
        return redirect('/admin/login/')

    errors = []
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            errors.append("Please enter both username and password.")
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_staff:
                    auth_login(request, user)
                    return redirect('/admin/')
                else:
                    errors.append("This account does not have administrator permissions.")
            else:
                errors.append("Invalid username or password. Please try again.")

    context = {
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
        'login_errors': errors,
    }
    return render(request, 'admin/login.html', context)


def admin_logout_view(request):
    """
    Handles logging out the user and safely redirecting to /admin/login/
    """
    logout(request)
    return redirect('/admin/login/')
