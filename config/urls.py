from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.controllers import setup_admin_customizations

# Initialize Admin site custom index and settings
setup_admin_customizations()

urlpatterns = [
    path('admin/', include('app.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
