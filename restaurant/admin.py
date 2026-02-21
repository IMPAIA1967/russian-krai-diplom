from django.contrib import admin
from .models import Category, MenuItem, Reservation, User


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'created_at']
    list_editable = ['order']
    ordering = ['order']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'created_at']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['guest_name', 'reservation_date', 'reservation_time', 'guests_count', 'status']
    list_filter = ['status', 'reservation_date']
    search_fields = ['guest_name', 'guest_phone', 'guest_email']
    ordering = ['-reservation_date', '-reservation_time']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_admin', 'is_active']
    list_filter = ['is_admin', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
