import uuid

from django.db import models


class Category(models.Model):
    """Категории меню"""
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        db_table = "categories"

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """Позиции меню ресторана"""
    name = models.CharField(max_length=200, verbose_name="Название блюда")
    description = models.TextField(verbose_name="Описание блюда")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.CharField(max_length=500, null=True, blank=True, verbose_name="Изображение")
    category = models.ForeignKey(
        Category,
        related_name="menu_items",
        on_delete=models.CASCADE,
        verbose_name="Категория"
    )
    is_available = models.BooleanField(default=True, verbose_name="Доступно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Позиция меню"
        verbose_name_plural = "Позиции меню"
        db_table = "menu_items"

    def __str__(self):
        return self.name


class Reservation(models.Model):
    """Бронирование столиков"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]

    guest_name = models.CharField(max_length=100, verbose_name="Имя гостя")
    guest_phone = models.CharField(max_length=20, verbose_name="Телефон")
    guest_email = models.CharField(max_length=200, verbose_name="Email")
    reservation_date = models.DateField(verbose_name="Дата бронирования")
    reservation_time = models.TimeField(verbose_name="Время бронирования")
    guests_count = models.IntegerField(default=2, verbose_name="Количество гостей")

    status = models.CharField(
        max_length=20,
        default='pending',
        choices=STATUS_CHOICES,
        verbose_name="Статус"
    )

    # Уникальный токен для подтверждения
    confirmation_token = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Токен подтверждения"
    )

    special_requests = models.TextField(null=True, blank=True, verbose_name="Особые пожелания")
    is_paid = models.BooleanField(default=False, verbose_name="Оплачено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        db_table = "reservations"

    def __str__(self):
        return f"{self.guest_name} - {self.reservation_date} {self.reservation_time}"

    def save(self, *args, **kwargs):
        # Генерируем токен при создании
        if not self.confirmation_token:
            import uuid
            self.confirmation_token = str(uuid.uuid4())
            print(f"Generated token: {self.confirmation_token}")  # Для отладки
        super().save(*args, **kwargs)

class User(models.Model):
    """Пользователь системы"""
    email = models.CharField(max_length=200, unique=True, verbose_name="Email")
    password = models.CharField(max_length=128, verbose_name="Пароль")
    first_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Фамилия")
    is_admin = models.BooleanField(default=False, verbose_name="Администратор")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        db_table = "users"

    def __str__(self):
        return self.email