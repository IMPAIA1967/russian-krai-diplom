from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Category, MenuItem, Reservation, User
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    ReservationSerializer,
    ReservationCreateSerializer,
    UserSerializer,
    LoginSerializer
)
from rest_framework.decorators import api_view
from rest_framework.response import Response


class CategoryViewSet(viewsets.ModelViewSet):
    """API контроллер для категорий меню."""
    queryset = Category.objects.all().order_by('order')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'created_at']


class MenuItemViewSet(viewsets.ModelViewSet):
    """API контроллер для позиций меню."""
    queryset = MenuItem.objects.all().order_by('category__order', 'name')
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'created_at']


class ReservationViewSet(viewsets.ModelViewSet):
    """API контроллер для бронирований."""
    queryset = Reservation.objects.all().order_by('-created_at')
    serializer_class = ReservationSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'reservation_date']
    ordering_fields = ['reservation_date', 'reservation_time', 'created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer



class RegisterView(APIView):
    """Контроллер для регистрации нового пользователя."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Пользователь успешно зарегистрирован"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Контроллер для входа пользователя и получения JWT токена."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = User.objects.filter(email=email).first()

            if user and check_password(password, user.password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            return Response({"error": "Неверный email или пароль"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """API контроллер для управления пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
def api_root(request):
    """
    Корневой endpoint API.
    Показывает доступные endpoints
    """
    return Response({
        'categories': '/api/categories/',
        'menu': '/api/menu/',
        'reservations': '/api/reservations/',
        'auth/register': '/api/auth/register/',
        'auth/login': '/api/auth/login/',
    }, headers={'Allow': 'GET, HEAD, OPTIONS'})

class IndexView(TemplateView):
    """Контроллер для главной страницы."""
    template_name = 'restaurant/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Главная'
        return context


class MenuView(TemplateView):
    """Контроллер для страницы меню."""
    template_name = 'restaurant/menu.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_items'] = MenuItem.objects.filter(is_available=True)
        context['categories'] = Category.objects.all().order_by('order')
        context['page_title'] = 'Меню'
        return context


class ReservationView(CreateView):
    """Контроллер для страницы бронирования."""
    template_name = 'restaurant/reservation.html'
    model = Reservation
    fields = ['guest_name', 'guest_phone', 'guest_email',
              'reservation_date', 'reservation_time',
              'guests_count', 'special_requests']
    success_url = reverse_lazy('reservation')

    def form_valid(self, form):
        messages.success(self.request, 'Ваша заявка успешно отправлена!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)