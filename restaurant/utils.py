from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_reservation_email(reservation):
    """Отправляет email ПОДТВЕРЖДЕНИЕ бронирования с кнопкой подтверждения"""
    subject = f'Бронирование столика от {reservation.guest_name}'

    # Генерируем ссылку для подтверждения
    confirm_url = f'{settings.SITE_URL}/reservation/confirm/{reservation.confirmation_token}/'

    print(f"=== send_reservation_email ===")
    print(f"Guest: {reservation.guest_name}")
    print(f"Token: {reservation.confirmation_token}")
    print(f"Confirm URL: {confirm_url}")

    # ✅ Рендерим HTML шаблон ПОДТВЕРЖДЕНИЯ (исправлено!)
    html_message = render_to_string('restaurant/emails/reservation_confirmation.html', {
        'reservation': reservation,
        'confirm_url': confirm_url,
    })

    # Текстовая версия
    text_message = f"""
    Ресторан "Русский Край" - Бронирование столика

    Данные гостя:
    - Имя: {reservation.guest_name}
    - Телефон: {reservation.guest_phone}
    - Email: {reservation.guest_email}

    Детали бронирования:
    - Дата: {reservation.reservation_date}
    - Время: {reservation.reservation_time}
    - Количество гостей: {reservation.guests_count}
    - Статус: {reservation.get_status_display()}
    - Оплачено: {'Да' if reservation.is_paid else 'Нет'}

    Подтвердить бронь: {confirm_url}

    ---
    Ресторан "Русский Край"
    """

    # Отправляем email
    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.guest_email],
        html_message=html_message,
        fail_silently=False,
    )

    print(f"=== Email sent to {reservation.guest_email} ===")


def send_cancellation_email(reservation):
    """Отправляет email УВЕДОМЛЕНИЕ об отмене бронирования"""
    subject = f'Бронирование отменено - {reservation.reservation_date}'

    print(f"=== send_cancellation_email ===")
    print(f"Guest: {reservation.guest_name}")

    # ✅ Рендерим HTML шаблон ОТМЕНЫ (исправлено!)
    html_message = render_to_string('restaurant/emails/reservation_cancellation.html', {
        'reservation': reservation,
    })

    # Текстовая версия
    text_message = f"""
    Ресторан "Русский Край" - Бронирование отменено

    Данные гостя:
    - Имя: {reservation.guest_name}
    - Телефон: {reservation.guest_phone}
    - Email: {reservation.guest_email}

    Детали бронирования:
    - Дата: {reservation.reservation_date}
    - Время: {reservation.reservation_time}
    - Количество гостей: {reservation.guests_count}

    Статус: Отменено

    ---
    Ресторан "Русский Край"
    """

    # Отправляем email
    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.guest_email],
        html_message=html_message,
        fail_silently=False,
    )

    print(f"=== Cancellation email sent to {reservation.guest_email} ===")