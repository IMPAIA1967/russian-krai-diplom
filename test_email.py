import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("\n📧 ТЕСТИРОВАНИЕ EMAIL...")
print("="*60)
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print("="*60)

# Твоё реальное email для теста
test_email = input("Введите email для теста (или нажмите Enter для использования EMAIL_HOST_USER): ").strip()
if not test_email:
    test_email = settings.EMAIL_HOST_USER

print(f"\nОтправляю тестовое письмо на: {test_email}")

try:
    send_mail(
        '🎓 ТЕСТОВОЕ ПИСЬМО от Django',
        'Если вы видите это письмо — email работает!\n\nРесторан "Русский Край"',
        settings.DEFAULT_FROM_EMAIL,
        [test_email],
        fail_silently=False,
    )
    print("\n✅ ПИСЬМО ОТПРАВЛЕНО УСПЕШНО!")
    print("📬 Проверьте почтовый ящик (и папку СПАМ)")
except Exception as e:
    print(f"\n❌ ОШИБКА ОТПРАВКИ:")
    print(f"   {e}")
    print(f"\nВозможные причины:")
    print("   1. Неверный EMAIL_HOST_PASSWORD")
    print("   2. Не включена двухфакторная аутентификация в Яндекс")
    print("   3. Не создан пароль приложения")
    print("   4. Брандмауэр блокирует порт 465")
    import traceback
    traceback.print_exc()

print("="*60 + "\n")