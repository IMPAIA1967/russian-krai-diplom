from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Category, MenuItem, Reservation, User, Review
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
from .utils import send_reservation_email, send_cancellation_email
from django.contrib.auth import login


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
    """Корневой endpoint API."""
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
        # Добавляем команду ресторана
        from .models import TeamMember, Review
        context['team_members'] = TeamMember.objects.filter(is_active=True).order_by('order', 'last_name')[:8]
        # Добавляем опубликованные отзывы
        context['reviews'] = Review.objects.filter(is_published=True).select_related()[:6]
        # Считаем средний рейтинг
        from django.db.models import Avg
        avg_rating = Review.objects.filter(is_published=True).aggregate(Avg('rating'))['rating__avg']
        context['average_rating'] = round(avg_rating, 1) if avg_rating else 0
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_reservations'] = Reservation.objects.filter(
                guest_email=self.request.user.email
            ).exclude(status='cancelled').order_by('-reservation_date', '-reservation_time')[:10]
        else:
            context['user_reservations'] = []
        return context

    def form_valid(self, form):
        """Вызывается при успешной валидации формы"""
        self.object = form.save(commit=False)
        self.object.status = 'pending'
        self.object.is_paid = False

        if not self.object.confirmation_token:
            import uuid
            self.object.confirmation_token = str(uuid.uuid4())

        self.object.save()

        try:
            send_reservation_email(self.object)
        except Exception as e:
            print(f"Email error: {e}")

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Бронирование успешно создано!'})

        messages.success(self.request, 'Бронирование успешно создано!')
        return super().form_valid(form)

    def form_invalid(self, form):
        """Вызывается при ошибке валидации"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
            }, status=400)
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


@api_view(['GET'])
def get_booked_times(request):
    """Возвращает забронированные времена для конкретной даты"""
    date_str = request.GET.get('date')

    if not date_str:
        return Response({'error': 'Дата не указана'}, status=status.HTTP_400_BAD_REQUEST)

    booked = Reservation.objects.filter(
        reservation_date=date_str,
        status__in=['pending', 'confirmed']
    ).values_list('reservation_time', flat=True)

    booked_times = [time.strftime('%H:%M') for time in booked]

    return Response({'booked_times': booked_times})


class ApiDocsView(TemplateView):
    """Страница документации API"""
    template_name = 'restaurant/api.html'


class CancelReservationView(View):
    """Контроллер для отмены бронирования."""

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)

        if reservation.is_paid:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Нельзя отменить оплаченную бронь.'
                }, status=400)
            messages.error(request, 'Нельзя отменить оплаченную бронь.')
            return redirect('profile')

        reservation.status = 'cancelled'
        reservation.save()

        try:
            send_cancellation_email(reservation)
        except Exception as e:
            print(f"Email error: {e}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Бронирование успешно отменено!'
            })

        messages.success(request, 'Бронирование отменено.')
        return redirect('profile')


class ConfirmReservationView(View):
    """Контроллер для подтверждения бронирования по токену."""

    def get(self, request, token):
        try:
            reservation = Reservation.objects.get(confirmation_token=token)

            if reservation.status == 'cancelled':
                messages.error(request, 'Это бронирование было отменено.')
                return redirect('reservation')

            if reservation.status == 'confirmed':
                messages.success(request, 'Ваша бронь уже подтверждена. Ждем вас!')
                return redirect('reservation')

            reservation.status = 'confirmed'
            reservation.save()

            messages.success(request, 'Ваша бронь подтверждена! Ждем вас!')
            return redirect('reservation')

        except Reservation.DoesNotExist:
            messages.error(request, 'Неверная ссылка подтверждения.')
            return redirect('reservation')


def profile_view(request):
    """
    Личный кабинет пользователя.
    Если не авторизован — показывает страницу входа/регистрации.
    Если авторизован — показывает профиль с бронированиями.
    """
    if request.user.is_authenticated:
        user_reservations = Reservation.objects.filter(
            guest_email=request.user.email
        ).exclude(status='cancelled').order_by('-reservation_date', '-reservation_time')

        active_count = user_reservations.count()

        return render(request, 'restaurant/profile.html', {
            'user_reservations': user_reservations,
            'active_count': active_count,
            'page_title': 'Профиль',
        })

    return render(request, 'restaurant/auth/login_register.html', {
        'page_title': 'Вход / Регистрация',
    })


def logout_view(request):
    """Выход из аккаунта"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('index')


def auth_register_login(request):
    """
    Единая страница регистрации и входа по телефону.
    """
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if not phone or not email:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
            return redirect('profile')

        user = User.objects.filter(phone=phone).first()

        if user:
            # Стандартный login()
            from django.contrib.auth import login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return redirect('profile')
        else:
            #  Новый пользователь — регистрируем
            from django.contrib.auth.hashers import make_password
            user = User.objects.create(
                email=email,
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                password=make_password(None),
                role='guest',
                is_active=True
            )
            messages.success(request, 'Регистрация успешна! Добро пожаловать!')

            # Стандартный login()
            from django.contrib.auth import login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return redirect('profile')

    return render(request, 'restaurant/auth/login_register.html', {
        'page_title': 'Вход / Регистрация',
    })


def submit_review(request):
    """
    Отправка отзыва гостем.
    """
    if request.method == 'POST':
        guest_name = request.POST.get('guest_name', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        rating = request.POST.get('rating', 5)
        text = request.POST.get('text', '').strip()

        if not guest_name or not guest_email or not text:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
            return redirect('index')

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except ValueError:
            messages.error(request, 'Некорректный рейтинг.')
            return redirect('index')

        Review.objects.create(
            guest_name=guest_name,
            guest_email=guest_email,
            rating=rating,
            text=text,
            is_published=False  # Требует модерации
        )

        messages.success(
            request,
            'Спасибо за отзыв! Он появится на сайте после модерации.'
        )
        return redirect('index#review-thanks') # якорь для модального окна

    return redirect('index')