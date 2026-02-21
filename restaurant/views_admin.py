from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Reservation, TeamMember, Review
from .decorators import admin_required
from .utils import send_reservation_email, send_cancellation_email


@admin_required
def admin_dashboard(request):
    """
    Главная страница админ-панели
    Показывает брони на сегодня и завтра
    """
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # Бронирования на сегодня
    today_reservations = Reservation.objects.filter(
        reservation_date=today
    ).order_by('reservation_time')

    # Бронирования на завтра
    tomorrow_reservations = Reservation.objects.filter(
        reservation_date=tomorrow
    ).order_by('reservation_time')

    # Статистика за неделю
    week_ago = today - timedelta(days=7)
    total_week = Reservation.objects.filter(
        reservation_date__gte=week_ago
    ).count()
    confirmed_week = Reservation.objects.filter(
        reservation_date__gte=week_ago,
        status='confirmed'
    ).count()
    cancelled_week = Reservation.objects.filter(
        reservation_date__gte=week_ago,
        status='cancelled'
    ).count()

    context = {
        'today_reservations': today_reservations,
        'tomorrow_reservations': tomorrow_reservations,
        'today_count': today_reservations.count(),
        'tomorrow_count': tomorrow_reservations.count(),
        'total_week': total_week,
        'confirmed_week': confirmed_week,
        'cancelled_week': cancelled_week,
    }

    return render(request, 'restaurant/admin/dashboard.html', context)


@admin_required
def admin_reservations(request):
    """
    Страница всех бронирований
    Можно фильтровать по статусу и дате
    """
    # Получаем все брони
    reservations = Reservation.objects.all().order_by('-reservation_date', '-reservation_time')

    # Фильтры из GET-параметров
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status:
        reservations = reservations.filter(status=status)
    if date_from:
        reservations = reservations.filter(reservation_date__gte=date_from)
    if date_to:
        reservations = reservations.filter(reservation_date__lte=date_to)

    context = {
        'reservations': reservations,
        'STATUS_CHOICES': Reservation.STATUS_CHOICES,
    }

    return render(request, 'restaurant/admin/reservations.html', context)


@admin_required
def admin_confirm_reservation(request, pk):
    """
    Подтверждение брони администратором
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    if reservation.status == 'cancelled':
        messages.error(request, 'Нельзя подтвердить отменённую бронь.')
    else:
        reservation.status = 'confirmed'
        reservation.save()
        messages.success(request, f'Бронь #{pk} подтверждена!')

        # Отправляем email клиенту
        try:
            send_reservation_email(reservation)
        except Exception as e:
            print(f"Email error: {e}")

    return redirect('admin_reservations')


@admin_required
def admin_cancel_reservation(request, pk):
    """
    Отмена брони администратором
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    reservation.status = 'cancelled'
    reservation.save()
    messages.success(request, f'Бронь #{pk} отменена.')

    # Отправляем email клиенту
    try:
        send_cancellation_email(reservation)
    except Exception as e:
        print(f"Email error: {e}")

    return redirect('admin_reservations')


@admin_required
def admin_statistics(request):
    """
    Страница статистики и аналитики
    """
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)

    # Статистика по статусам
    status_stats = Reservation.objects.values('status').annotate(
        count=Count('id')
    )

    # Статистика по дням (последние 30 дней)
    daily_stats = Reservation.objects.filter(
        reservation_date__gte=month_ago
    ).values('reservation_date').annotate(
        count=Count('id'),
        guests=Sum('guests_count')
    ).order_by('reservation_date')

    # Общая статистика
    total_reservations = Reservation.objects.count()
    total_guests = Reservation.objects.aggregate(
        total=Sum('guests_count')
    )['total'] or 0

    context = {
        'status_stats': status_stats,
        'daily_stats': daily_stats,
        'total_reservations': total_reservations,
        'total_guests': total_guests,
    }

    return render(request, 'restaurant/admin/statistics.html', context)


def admin_team(request):
    """
    Страница управления командой ресторана.
    """
    if not (request.user.is_authenticated and request.user.is_staff_user):
        messages.error(request, 'Доступ запрещён. Только для сотрудников.')
        return redirect('index')

    team_members = TeamMember.objects.all().order_by('order', 'last_name')

    return render(request, 'restaurant/admin/team.html', {
        'team_members': team_members,
        'page_title': 'Команда ресторана',
    })


def admin_add_team_member(request):
    """
    Добавление нового члена команды.
    """
    if not (request.user.is_authenticated and request.user.is_staff_user):
        messages.error(request, 'Доступ запрещён. Только для сотрудников.')
        return redirect('index')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        position = request.POST.get('position', '').strip()
        custom_position = request.POST.get('custom_position', '').strip()
        photo = request.POST.get('photo', '').strip()
        description = request.POST.get('description', '').strip()
        bio = request.POST.get('bio', '').strip()
        instagram = request.POST.get('instagram', '').strip()
        telegram = request.POST.get('telegram', '').strip()
        order = request.POST.get('order', 0)
        is_active = request.POST.get('is_active') == 'on'

        if not first_name or not last_name or not position or not description:
            messages.error(request, 'Заполните обязательные поля: Имя, Фамилия, Должность, Описание')
            return redirect('admin_team')

        TeamMember.objects.create(
            first_name=first_name,
            last_name=last_name,
            position=position,
            custom_position=custom_position or None,
            photo=photo or None,
            description=description,
            bio=bio or None,
            instagram=instagram or None,
            telegram=telegram or None,
            order=int(order) if order else 0,
            is_active=is_active
        )

        messages.success(request, f'Член команды {first_name} {last_name} добавлен!')
        return redirect('admin_team')

    return redirect('admin_team')


def admin_edit_team_member(request, pk):
    """
    Редактирование члена команды.
    """
    if not (request.user.is_authenticated and request.user.is_staff_user):
        messages.error(request, 'Доступ запрещён. Только для сотрудников.')
        return redirect('index')

    member = get_object_or_404(TeamMember, pk=pk)

    if request.method == 'POST':
        member.first_name = request.POST.get('first_name', '').strip()
        member.last_name = request.POST.get('last_name', '').strip()
        member.position = request.POST.get('position', '').strip()
        member.custom_position = request.POST.get('custom_position', '').strip() or None
        member.photo = request.POST.get('photo', '').strip() or None
        member.description = request.POST.get('description', '').strip()
        member.bio = request.POST.get('bio', '').strip() or None
        member.instagram = request.POST.get('instagram', '').strip() or None
        member.telegram = request.POST.get('telegram', '').strip() or None
        member.order = int(request.POST.get('order', 0))
        member.is_active = request.POST.get('is_active') == 'on'
        member.save()

        messages.success(request, f'Данные {member.first_name} {member.last_name} обновлены!')
        return redirect('admin_team')

    return redirect('admin_team')


def admin_delete_team_member(request, pk):
    """
    Удаление члена команды.
    """
    if not (request.user.is_authenticated and request.user.is_staff_user):
        messages.error(request, 'Доступ запрещён. Только для сотрудников.')
        return redirect('index')

    member = get_object_or_404(TeamMember, pk=pk)
    member.delete()

    messages.success(request, f'Член команды удалён!')
    return redirect('admin_team')


def admin_reviews(request):
    """
    Страница управления отзывами (модерация).
    """
    if not (request.user.is_authenticated and request.user.is_staff_user):
        messages.error(request, 'Доступ запрещён. Только для сотрудников.')
        return redirect('index')

    status_filter = request.GET.get('status', 'all')

    if status_filter == 'published':
        reviews = Review.objects.filter(is_published=True)
    elif status_filter == 'pending':
        reviews = Review.objects.filter(is_published=False)
    else:
        reviews = Review.objects.all()

    reviews = reviews.order_by('-created_at')

    return render(request, 'restaurant/admin/reviews.html', {
        'reviews': reviews,
        'status_filter': status_filter,
        'page_title': 'Модерация отзывов',
    })


def admin_publish_review(request, pk):
    """
    Опубликовать отзыв.
    """
    if not (request.user.is_authenticated and request.user.is_staff_user):
        messages.error(request, 'Доступ запрещён.')
        return redirect('index')

    review = get_object_or_404(Review, pk=pk)
    review.is_published = True
    review.save()

    messages.success(request, f'Отзыв от {review.guest_name} опубликован!')
    return redirect('admin_reviews')


def admin_unpublish_review(request, pk):
    """
    Снять с публикации отзыв.
    """
    if not (request.user.is_authenticated and request.user.is_staff_user):
        messages.error(request, 'Доступ запрещён.')
        return redirect('index')

    review = get_object_or_404(Review, pk=pk)
    review.is_published = False
    review.save()

    messages.success(request, f'Отзыв от {review.guest_name} снят с публикации.')
    return redirect('admin_reviews')


def admin_delete_review(request, pk):
    """
    Удалить отзыв.
    """
    if not (request.user.is_authenticated and request.user.is_staff_user):
        messages.error(request, 'Доступ запрещён.')
        return redirect('index')

    review = get_object_or_404(Review, pk=pk)
    review.delete()

    messages.success(request, 'Отзыв удалён!')
    return redirect('admin_reviews')