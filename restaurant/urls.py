from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .models import Reservation
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
    ApiDocsView,
    CancelReservationView, profile_view, get_booked_times, ConfirmReservationView, logout_view, auth_register_login,
)
from .views_admin import admin_dashboard, admin_reservations, admin_statistics, admin_cancel_reservation, \
    admin_confirm_reservation, admin_team, admin_edit_team_member, admin_add_team_member, admin_delete_team_member


@api_view(['GET'])
def get_booked_times(request):
    """Возвращает забронированные времена для конкретной даты"""
    date_str = request.GET.get('date')

    if not date_str:
        return Response({'error': 'Дата не указана'}, status=400)

    booked = Reservation.objects.filter(
        reservation_date=date_str,
        status__in=['pending', 'confirmed']
    ).values_list('reservation_time', flat=True)

    booked_times = [time.strftime('%H:%M') for time in booked]

    return Response({'booked_times': booked_times})

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menu-item')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'users', UserViewSet, basename='user')

web_urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('menu/', MenuView.as_view(), name='menu'),
    path('reservation/', ReservationView.as_view(), name='reservation'),
    path('reservation/<int:pk>/cancel/', CancelReservationView.as_view(), name='cancel_reservation'),
    path('reservation/confirm/<str:token>/', ConfirmReservationView.as_view(), name='confirm_reservation'),

    # Маршруты для авторизации
    path('profile/', profile_view, name='profile'),
    path('auth/register-login/', auth_register_login, name='auth_register_login'),
    path('auth/logout/', logout_view, name='logout'),

    # Маршруты для админ-панели
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    path('admin-panel/reservations/', admin_reservations, name='admin_reservations'),
    path('admin-panel/reservations/<int:pk>/confirm/', admin_confirm_reservation, name='admin_confirm_reservation'),
    path('admin-panel/reservations/<int:pk>/cancel/', admin_cancel_reservation, name='admin_cancel_reservation'),
    path('admin-panel/statistics/', admin_statistics, name='admin_statistics'),

    # Маршруты для управления командой
    path('admin-panel/team/', admin_team, name='admin_team'),
    path('admin-panel/team/add/', admin_add_team_member, name='admin_add_team_member'),
    path('admin-panel/team/<int:pk>/edit/', admin_edit_team_member, name='admin_edit_team_member'),
    path('admin-panel/team/<int:pk>/delete/', admin_delete_team_member, name='admin_delete_team_member'),

    path('api/booked-times/', get_booked_times, name='get_booked_times'),
]

api_urlpatterns = [
    path('', api_root, name='api-root'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('profile/', profile_view, name='profile'),
]

urlpatterns = web_urlpatterns + [
    path('api/', include(router.urls)),
    path('api/auth/register/', RegisterView.as_view(), name='api-register'),
    path('api/auth/login/', LoginView.as_view(), name='api-login'),
]