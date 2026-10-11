import os
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-this-secret")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "receipts.apps.ReceiptsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
try:
    from importlib.util import find_spec

    if find_spec("whitenoise"):
        MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
except ModuleNotFoundError:
    pass

ROOT_URLCONF = "lucky_receipt.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "receipts.context_processors.campaign_dates",
            ],
        },
    },
]

WSGI_APPLICATION = "lucky_receipt.wsgi.application"
DATABASE_ENGINE = os.getenv("DATABASE_ENGINE", "django.db.backends.postgresql")
if DATABASE_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {"default": {"ENGINE": DATABASE_ENGINE, "NAME": os.getenv("SQLITE_NAME", str(BASE_DIR / "local.sqlite3"))}}
else:
    DATABASES = {
        "default": {
            "ENGINE": DATABASE_ENGINE,
            "NAME": os.getenv("POSTGRES_DB", "lucky_receipt"),
            "USER": os.getenv("POSTGRES_USER", "lucky_receipt"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "change-me"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = os.getenv("CAMPAIGN_TIME_ZONE", "Europe/Moscow")
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE_BACKEND = "whitenoise.storage.CompressedManifestStaticFilesStorage"
try:
    if not find_spec("whitenoise"):
        STATICFILES_STORAGE_BACKEND = "django.contrib.staticfiles.storage.StaticFilesStorage"
except (NameError, ModuleNotFoundError):
    STATICFILES_STORAGE_BACKEND = "django.contrib.staticfiles.storage.StaticFilesStorage"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": STATICFILES_STORAGE_BACKEND},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "receipt_list"
LOGOUT_REDIRECT_URL = "login"

CAMPAIGN_TIME_ZONE = TIME_ZONE
CAMPAIGN_START_DATE = date.fromisoformat(os.getenv("CAMPAIGN_START_DATE", "2026-01-01"))
CAMPAIGN_END_DATE = date.fromisoformat(os.getenv("CAMPAIGN_END_DATE", "2026-12-31"))
if CAMPAIGN_START_DATE > CAMPAIGN_END_DATE:
    raise ValueError("CAMPAIGN_START_DATE must be on or before CAMPAIGN_END_DATE")
