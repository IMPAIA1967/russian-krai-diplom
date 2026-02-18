from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    CategoryViewSet,
    MenuItemViewSet,
    ReservationViewSet,
    RegisterView,
    LoginView,
    UserViewSet
)

# Создаём роутер
router = DefaultRouter()

# Регистрируем наши ViewSet'ы
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu', MenuItemViewSet, basename='menu-item')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'users', UserViewSet, basename='user')

# Получаем все URL-адреса
urlpatterns = router.urls

# Добавляем URL для аутентификации
urlpatterns += [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
]