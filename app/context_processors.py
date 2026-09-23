import os
from django.conf import settings
from app.models import Setting


def site_settings(request):
    """
    Context processor to make global site settings (logo, favicon, title)
    available across all templates.
    """
    try:
        site_logo = Setting.get_value('site_logo', default='')
        site_favicon = Setting.get_value('site_favicon', default='')
        site_header_title = Setting.get_value('site_header_title', default='Master Admin Panel')
        admin_email = Setting.get_value('admin_email', default='admin@gmail.com')

        media_url = settings.MEDIA_URL
        if not media_url.endswith('/'):
            media_url = f"{media_url}/"

        site_logo_url = f"{media_url}{site_logo}" if site_logo else None
        site_favicon_url = f"{media_url}{site_favicon}" if site_favicon else None

        return {
            'site_logo': site_logo,
            'site_logo_url': site_logo_url,
            'site_favicon': site_favicon,
            'site_favicon_url': site_favicon_url,
            'site_header_title': site_header_title,
            'site_admin_email': admin_email,
        }
    except Exception:
        return {
            'site_logo': None,
            'site_logo_url': None,
            'site_favicon': None,
            'site_favicon_url': None,
            'site_header_title': 'Master Admin Panel',
            'site_admin_email': 'admin@gmail.com',
        }
