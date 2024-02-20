from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from . import settings
from .spectacular import urlpatterns as api_documentation


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('recipes.urls', namespace='recipes')),
    path('api/', include('users.urls'))
] + api_documentation

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
