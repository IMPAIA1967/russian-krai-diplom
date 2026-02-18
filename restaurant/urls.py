from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    # API ViewSets
    CategoryViewSet,
    MenuItemViewSet,
    ReservationViewSet,
    RegisterView,
    LoginView,
    UserViewSet,
    # Template Views
    IndexView,
    MenuView,
    ReservationView,
)

# Создаём роутер для API
router = DefaultRouter()

# Регистрируем API endpoints
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu', MenuItemViewSet, basename='menu-item')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'users', UserViewSet, basename='user')

# Получаем все API URL-адреса
api_urlpatterns = router.urls

# URL для веб-страниц (Templates)
web_urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('menu/', MenuView.as_view(), name='menu'),
    path('reservation/', ReservationView.as_view(), name='reservation'),
]

# Объединяем API и веб-URL
urlpatterns = web_urlpatterns + [
    path('api/', include(api_urlpatterns)),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
]