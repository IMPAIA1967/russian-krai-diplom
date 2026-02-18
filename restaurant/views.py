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
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import User
from .serializers import UserSerializer, LoginSerializer
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Reservation


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


class RegisterView(APIView):
    """
    Контроллер для регистрации нового пользователя.
    Метод: POST
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Пользователь успешно зарегистрирован"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Контроллер для входа пользователя и получения JWT токена.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            # Ищем пользователя
            user = User.filter(email=email).first()

            if user and check_password(password, user.password):
                # Генерируем JWT токены
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            return Response({"error": "Неверный email или пароль"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    API контроллер для управления пользователями (только для админов).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только себя, если не админ
        if self.request.user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class IndexView(TemplateView):
    """
    Контроллер для главной страницы.
    Использует CBV (Class-Based View)
    """
    template_name = 'restaurant/index.html'

    def get_context_data(self, **kwargs):
        """Добавляем дополнительные данные в шаблон"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Главная'
        return context


class MenuView(TemplateView):
    """
    Контроллер для страницы меню.
    Получает данные из базы данных и передаёт в шаблон
    """
    template_name = 'restaurant/menu.html'

    def get_context_data(self, **kwargs):
        """Добавляем блюда из базы данных"""
        context = super().get_context_data(**kwargs)
        # Получаем все доступные блюда из базы
        context['menu_items'] = MenuItem.objects.filter(is_available=True)
        context['categories'] = Category.objects.all().order_by('order')
        context['page_title'] = 'Меню'
        return context


class ReservationView(CreateView):
    """
    Контроллер для страницы бронирования.
    Обрабатывает форму и сохраняет данные в базу
    """
    template_name = 'restaurant/reservation.html'
    model = Reservation
    fields = ['guest_name', 'guest_phone', 'guest_email',
              'reservation_date', 'reservation_time',
              'guests_count', 'special_requests']
    success_url = reverse_lazy('reservation')

    def form_valid(self, form):
        """Вызывается при успешной валидации формы"""
        messages.success(self.request, 'Ваша заявка успешно отправлена!')

        # Здесь будет отправка email и Telegram уведомления


        return super().form_valid(form)

    def form_invalid(self, form):
        """Вызывается при ошибке валидации"""
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)