import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User"""

    def create_user(self, email, phone=None, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')

        user = self.model(
            email=email,
            phone=phone,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(email, phone, password, **extra_fields)


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
        if not self.confirmation_token:
            self.confirmation_token = str(uuid.uuid4())
        super().save(*args, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь системы"""
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('staff', 'Сотрудник'),
        ('guest', 'Гость'),
    ]

    email = models.CharField(max_length=200, unique=True, verbose_name="Email")
    first_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Фамилия")
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Телефон")

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='guest',
        verbose_name="Роль"
    )

    is_admin = models.BooleanField(default=False, verbose_name="Администратор")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_staff = models.BooleanField(default=False, verbose_name="Staff статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        db_table = "users"

    def __str__(self):
        return self.email

    @property
    def is_staff_user(self):
        """Проверка: является ли пользователем ресторана (админ или сотрудник)"""
        return self.role in ['admin', 'staff'] or self.is_admin


class TeamMember(models.Model):
    """Члены команды ресторана"""
    POSITION_CHOICES = [
        ('chef', 'Шеф-повар'),
        ('sous_chef', 'Су-шеф'),
        ('manager', 'Менеджер'),
        ('waiter', 'Официант'),
        ('bartender', 'Бармен'),
        ('host', 'Хостес'),
        ('other', 'Другое'),
    ]

    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        verbose_name="Должность"
    )
    custom_position = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Другая должность"
    )
    photo = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Фото (URL)"
    )
    description = models.TextField(verbose_name="Описание")
    bio = models.TextField(null=True, blank=True, verbose_name="Биография")

    # Социальные сети
    instagram = models.CharField(max_length=200, null=True, blank=True, verbose_name="Instagram")
    telegram = models.CharField(max_length=200, null=True, blank=True, verbose_name="Telegram")

    # Порядок отображения
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Член команды"
        verbose_name_plural = "Члены команды"
        db_table = "team_members"
        ordering = ['order', 'last_name', 'first_name']

    def __str__(self):
        position = self.get_position_display()
        if self.custom_position:
            position = self.custom_position
        return f"{self.first_name} {self.last_name} - {position}"


class Review(models.Model):
    """Отзывы гостей ресторана"""
    RATING_CHOICES = [
        (1, '⭐ - Ужасно'),
        (2, '⭐⭐ - Плохо'),
        (3, '⭐⭐⭐ - Нормально'),
        (4, '⭐⭐⭐⭐ - Хорошо'),
        (5, '⭐⭐⭐⭐⭐ - Отлично'),
    ]

    guest_name = models.CharField(max_length=100, verbose_name="Имя гостя")
    guest_email = models.CharField(max_length=200, verbose_name="Email")
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        default=5,
        verbose_name="Рейтинг"
    )
    text = models.TextField(verbose_name="Текст отзыва")

    is_published = models.BooleanField(default=False, verbose_name="Опубликован")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        db_table = "reviews"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.guest_name} - {self.rating} ⭐"

    def get_rating_stars(self):
        """Возвращает строку со звёздами"""
        return '⭐' * self.rating


