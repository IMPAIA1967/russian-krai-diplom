from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Декоратор для защиты админ-панели.
    Проверяет что пользователь авторизован и имеет роль admin/staff
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 1. Проверяем авторизацию
        if not request.user.is_authenticated:
            messages.error(request, 'Пожалуйста, войдите в систему.')
            return redirect('login')

        # 2. Проверяем роль (admin или staff)
        user_role = getattr(request.user, 'role', 'guest')
        is_admin = getattr(request.user, 'is_admin', False)

        if user_role not in ['admin', 'staff'] and not is_admin:
            messages.error(request, 'Доступ запрещён. Только для сотрудников ресторана.')
            return redirect('index')

        # 3. Всё ок — вызываем view
        return view_func(request, *args, **kwargs)

    return wrapper
