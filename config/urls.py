from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('restaurant.urls')),  # Веб-страницы на корне
    path('api/', include('restaurant.urls')),  # API на /api/
    path('api-auth/', include('rest_framework.urls')),
]

# Добавляем поддержку медиа-файлов для разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)