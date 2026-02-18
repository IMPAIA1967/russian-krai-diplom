from tortoise import fields, models


class Category(models.Model):
    """Категории меню (например: Закуски, Основные блюда, Напитки)"""
    name = fields.CharField(max_length=100, verbose_name="Название категории")
    description = fields.TextField(null=True, verbose_name="Описание")
    order = fields.IntField(default=0, verbose_name="Порядок отображения")
    created_at = fields.DatetimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        table = "categories"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """Позиции меню ресторана"""
    name = fields.CharField(max_length=200, verbose_name="Название блюда")
    description = fields.TextField(verbose_name="Описание блюда")
    price = fields.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = fields.CharField(max_length=500, null=True, verbose_name="Изображение")
    category = fields.ForeignKeyField(
        "models.Category",
        related_name="menu_items",
        on_delete=fields.CASCADE,
        verbose_name="Категория"
    )
    is_available = fields.BooleanField(default=True, verbose_name="Доступно")
    created_at = fields.DatetimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = fields.DatetimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        table = "menu_items"
        verbose_name = "Позиция меню"
        verbose_name_plural = "Позиции меню"

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

    guest_name = fields.CharField(max_length=100, verbose_name="Имя гостя")
    guest_phone = fields.CharField(max_length=20, verbose_name="Телефон")
    guest_email = fields.CharField(max_length=200, verbose_name="Email")
    reservation_date = fields.DateField(verbose_name="Дата бронирования")
    reservation_time = fields.TimeField(verbose_name="Время бронирования")
    guests_count = fields.IntField(default=2, verbose_name="Количество гостей")
    status = fields.CharField(max_length=20, default='pending', choices=STATUS_CHOICES, verbose_name="Статус")
    special_requests = fields.TextField(null=True, verbose_name="Особые пожелания")
    created_at = fields.DatetimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = fields.DatetimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        table = "reservations"
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"

    def __str__(self):
        return f"{self.guest_name} - {self.reservation_date} {self.reservation_time}"
