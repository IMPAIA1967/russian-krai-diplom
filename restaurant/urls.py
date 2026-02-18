from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    # API Root
    api_root,
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

# Создаём API роутер
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu', MenuItemViewSet, basename='menu-item')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'users', UserViewSet, basename='user')

# Веб-страницы (Templates)
web_urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('menu/', MenuView.as_view(), name='menu'),
    path('reservation/', ReservationView.as_view(), name='reservation'),
]

# API endpoints
api_urlpatterns = [
    path('', api_root, name='api-root'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
]

# Объединяем всё
urlpatterns = web_urlpatterns + [
    path('api/', include((router.urls, 'api'), namespace='api')),
    path('api/auth/', include((api_urlpatterns[1:], 'auth'), namespace='auth')),
]