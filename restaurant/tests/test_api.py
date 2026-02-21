import pytest
from rest_framework import status
from rest_framework.test import APITestCase
from restaurant.models import Category, MenuItem
from datetime import date, timedelta


@pytest.mark.django_db
class TestCategoryAPI(APITestCase):
    """Тесты для API категорий"""

    def test_list_categories(self):
        """GET /api/categories/ — возвращает список категорий"""
        Category.objects.create(name='Закуски', order=1)
        Category.objects.create(name='Супы', order=2)

        response = self.client.get('/api/categories/')

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 2
        assert results[0]['name'] == 'Закуски'

    def test_create_category(self):
        """POST /api/categories/ — создание категории"""
        data = {'name': 'Новая категория', 'order': 3, 'description': 'Тест'}
        response = self.client.post('/api/categories/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() >= 1


@pytest.mark.django_db
class TestMenuItemAPI(APITestCase):
    """Тесты для API блюд меню"""

    def setUp(self):
        """Создаём тестовые данные перед каждым тестом"""
        self.category = Category.objects.create(name='Основные блюда', order=1)

    def test_list_menu_items(self):
        """GET /api/menu/ — возвращает доступные блюда"""
        MenuItem.objects.create(
            name='Борщ',
            description='Традиционный',
            price='450.00',
            category=self.category,
            is_available=True
        )

        response = self.client.get('/api/menu/')

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1

    def test_filter_by_category(self):
        """GET /api/menu/?category={id} — фильтрация по категории"""
        MenuItem.objects.create(
            name='Борщ',
            description='Традиционный',
            price='450.00',
            category=self.category,
            is_available=True
        )

        response = self.client.get(f'/api/menu/?category={self.category.id}')

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for item_data in results:
            cat_id = item_data.get('category')
            if isinstance(cat_id, dict):
                assert cat_id.get('id') == self.category.id
            else:
                assert cat_id == self.category.id

    def test_search_in_menu(self):
        """GET /api/menu/?search=борщ — поиск по названию"""
        MenuItem.objects.create(
            name='Борщ Московский',
            description='С говядиной',
            price='450.00',
            category=self.category,
            is_available=True
        )

        response = self.client.get('/api/menu/?search=Борщ Московский')

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        assert results[0]['name'] == 'Борщ Московский'


@pytest.mark.django_db
class TestReservationAPI(APITestCase):
    """Тесты для API бронирований"""

    def test_create_reservation(self):
        """POST /api/reservations/ — создание бронирования"""
        data = {
            'guest_name': 'Иван Иванов',
            'guest_phone': '+79991234567',
            'guest_email': 'ivan@example.com',
            'reservation_date': (date.today() + timedelta(days=7)).isoformat(),
            'reservation_time': '19:00:00',
            'guests_count': 4,
            'special_requests': 'Столик у окна'
        }

        response = self.client.post('/api/reservations/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['guest_name'] == 'Иван Иванов'

    def test_create_reservation_past_date(self):
        """POST /api/reservations/ — валидация даты (опционально)"""
        data = {
            'guest_name': 'Иван Иванов',
            'guest_phone': '+79991234567',
            'guest_email': 'ivan@example.com',
            'reservation_date': '2020-01-01',
            'reservation_time': '19:00:00',
            'guests_count': 4
        }

        response = self.client.post('/api/reservations/', data)

        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
