from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('restaurant.urls')),  # Подключаем наше API
    path('api-auth/', include('rest_framework.urls')),  # Страница входа DRF
]