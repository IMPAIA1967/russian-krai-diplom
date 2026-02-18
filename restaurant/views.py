from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, MenuItem, Reservation
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    ReservationSerializer,
    ReservationCreateSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API контроллер для категорий меню.
    Поддерживает: list, create, retrieve, update, partial_update, destroy
    """
    queryset = Category.objects.all().order_by('order')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]  # Доступно всем (на чтение)
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'created_at']


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    API контроллер для позиций меню.
    Поддерживает: list, create, retrieve, update, partial_update, destroy
    """
    queryset = MenuItem.objects.all().order_by('category__order', 'name')
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]  # Доступно всем (на чтение)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'created_at']


class ReservationViewSet(viewsets.ModelViewSet):
    """
    API контроллер для бронирований.
    Поддерживает: list, create, retrieve, update, partial_update, destroy
    """
    queryset = Reservation.objects.all().order_by('-created_at')
    permission_classes = [AllowAny]  # Пока доступно всем (потом добавим JWT)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'reservation_date']
    ordering_fields = ['reservation_date', 'reservation_time', 'created_at']

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия"""
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer

    def create(self, request, *args, **kwargs):
        """
        Переопределяем метод create для отправки уведомления
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Здесь будет логика отправки email/Telegram
        # send_reservation_notification(serializer.instance)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
