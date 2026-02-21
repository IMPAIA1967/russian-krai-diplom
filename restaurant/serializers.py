from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Category, MenuItem, Reservation
from django.contrib.auth.hashers import make_password


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий меню"""
    menu_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'order', 'created_at', 'menu_items_count']
        read_only_fields = ['created_at']

    def get_menu_items_count(self, obj):
        return obj.menu_items.all().count()


class MenuItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций меню"""
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'image',
            'category', 'category_name', 'is_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ReservationSerializer(serializers.ModelSerializer):
    """Сериализатор для бронирований"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'guest_name', 'guest_phone', 'guest_email',
            'reservation_date', 'reservation_time', 'guests_count',
            'status', 'status_display', 'special_requests',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

    def validate_guests_count(self, value):
        if value < 1 or value > 20:
            raise serializers.ValidationError("Количество гостей должно быть от 1 до 20")
        return value

    def validate(self, data):
        # Проверка, что дата не в прошлом
        from datetime import date
        if data.get('reservation_date') and data['reservation_date'] < date.today():
            raise serializers.ValidationError("Нельзя забронировать столик в прошлом")
        return data


class ReservationCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания бронирования (клиентский)"""
    class Meta:
        model = Reservation
        fields = [
            'guest_name', 'guest_phone', 'guest_email',
            'reservation_date', 'reservation_time', 'guests_count',
            'special_requests'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей"""
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'is_admin', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        """Хешируем пароль перед сохранением"""
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа пользователя"""
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
