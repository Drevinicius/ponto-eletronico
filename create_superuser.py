# create_superuser.py
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ponto.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def create_superuser():
    # Dados do superuser - ALTERE AQUI!
    username = "admin"
    email = "admin@empresa.com"
    password = "123"  # ⚠️ ALTERE PARA UMA SENHA SEGURA!

    # Verificar se já existe
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Superuser '{username}' criado com sucesso!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
    else:
        print("ℹ️ Superuser já existe!")


if __name__ == "__main__":
    create_superuser()