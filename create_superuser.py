# create_superuser.py
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ponto.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def create_superuser():
    username = os.environ.get('SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('SUPERUSER_EMAIL', 'admin@empresa.com')
    password = os.environ.get('SUPERUSER_PASSWORD', 'Admin123!')

    if not username or not password:
        print("❌ Variáveis de superuser não configuradas")
        return

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Superuser '{username}' criado com sucesso!")
    else:
        print(f"ℹ️ Superuser '{username}' já existe!")


if __name__ == "__main__":
    create_superuser()