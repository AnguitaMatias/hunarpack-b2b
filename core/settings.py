"""
Django settings for core project.
"""

from pathlib import Path
import os
import dj_database_url
import cloudinary
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

# =====================================================================================
# 1. RUTAS Y SEGURIDAD
# =====================================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')

# En render, DEBUG será 'False'
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Permitir todos los host (<- no olvidar modificar al dominio cuando lo compre)
ALLOWED_HOSTS = ['*']

# Dominios de confianza para CSRF (los formularios)
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'http://*.onrender.com',
]

# =====================================================================================
# 2. APLICACIONES INSTALADAS
# =====================================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'catalogo',
    'django.contrib.humanize',
]

# =====================================================================================
# 3. MIDDLEWARES
# =====================================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =====================================================================================
# 4. URLS Y TEMPLATES
# =====================================================================================
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'catalogo.context_processors.contador_carrito'
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# =====================================================================================
# 5. BASE DE DATOS
# =====================================================================================
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# =====================================================================================
# 6. VALIDACIÓN DE CONTRASEÑAS
# =====================================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =====================================================================================
# 7. INTERNACIONALIZACIÓN
# =====================================================================================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

# =====================================================================================
# 8. ARCHIVOS ESTÁTICOS Y MULTIMEDIA
# =====================================================================================
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'

# =====================================================================================
# 9. CONFIGURACIÓN DE CORREO
# =====================================================================================
if os.environ.get('EMAIL_USE_REAL_SMTP') == 'True':
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'OPTIONS': {
                'host': 'smtp.gmail.com',
                'port': 587,
                'username': os.environ.get('EMAIL_HOST_USER'),
                'password': os.environ.get('EMAIL_HOST_PASSWORD'),
                'use_tls':  True,
            },
        },
    }
else:
    # Config del correo para desarrollo
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.console.EmailBackend',
        },
    }

DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', 'ventas@hunarpack.cl')

# =====================================================================================
# 10. CONFIGURACIÓN DE CLOUDINARY Y STORAGES
# =====================================================================================
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

STORAGES = {
    # Config para los archivos subidos por el usuario (img productos, categorías, etc.)
    'default':{
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    # Config para los archivos estáticos (CSS, JS, logo, favicon, etc.)
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    },
}

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# =====================================================================================
# 11. AUTENTICACIÓN Y REDIRECCIONES
# =====================================================================================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = 'lista_categorias'
LOGOUT_REDIRECT_URL = 'lista_categorias'


# --- LOGGING PARA PRODUCCIÓN ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
