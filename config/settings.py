from pathlib import Path
from decouple import config, Csv

# ========================
# Rutas base
# ========================
BASE_DIR = Path(__file__).resolve().parent.parent

# ========================
# Formatos locales
# ========================
FORMAT_MODULE_PATH = ['config.formats']

# ========================
# Seguridad básica
# ========================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

# ========================
# Aplicaciones instaladas
# ========================
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',                # <-- requerido por allauth

    # Autenticación social (Google)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Tus apps
    'docs',
    'accounts',
    'main',
    'major_equipment',
    'firebrigade',
]

SITE_ID = 1  # Ajusta el registro en Admin -> Sites (localhost:8000 en dev, dominio real en prod)

# ========================
# Middleware
# ========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  
    'allauth.account.middleware.AccountMiddleware',              
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'

# ========================
# Templates
# ========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],  # sobrescribe allauth con tu /templates/account/login.html si quieres
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # <-- requerido por allauth
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.context_processors.site_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ========================
# Base de datos
# ========================
USE_SQLITE = config('USE_SQLITE', default=True, cast=bool)
if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME':     config('DB_NAME'),
            'USER':     config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST':     config('DB_HOST'),
            'PORT':     config('DB_PORT', cast=int),
        }
    }

# ========================
# Archivos estáticos y media
# ========================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ========================
# Correo
# ========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='cbq.informatica@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ========================
# Seguridad en producción
# ========================
if not DEBUG:
    # HSTS (1 año)
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # HTTPS forzado
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Cookies seguras
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Mitigaciones XSS / sniffing
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Clickjacking
    X_FRAME_OPTIONS = 'DENY'

    CSRF_TRUSTED_ORIGINS = [
        "https://bomberosquintero.cl",
        "https://www.bomberosquintero.cl",
    ]

    FILE_UPLOAD_PERMISSIONS = 0o664
    FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o775
else:
    # En dev puedes permitir orígenes locales vía .env si prefieres:
    # CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
    pass

# ========================
# Logging
# ========================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'major_equipment': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ========================
# Internacionalización y formatos
# ========================
USE_I18N = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_TZ = True

# ========================
# Autenticación (se mantiene tu backend + Google)
# ========================
AUTHENTICATION_BACKENDS = [
    'firebrigade.backends.RolePermissionBackend',              # tu backend
    'django.contrib.auth.backends.ModelBackend',               # clásico
    'allauth.account.auth_backends.AuthenticationBackend',     # Google
]

# Config de allauth
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_METHODS = {'username', 'email'}  # permite login local con usuario o email
ACCOUNT_SIGNUP_ENABLED = False  # sin registro público
SOCIALACCOUNT_LOGIN_ON_GET = True

# Google (OIDC)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['openid', 'email', 'profile'],
        'AUTH_PARAMS': {'prompt': 'select_account', 'hd': 'bomberosquintero.cl'},
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),
            'key': '',
        },
    }
}

# Adapter para limitar acceso al dominio corporativo
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.DomainRestrictedAdapter'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
