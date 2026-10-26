from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent
# Local classroom demonstration; no authentication or user data is stored.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-grpc-dice-demo-only")
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
ROOT_URLCONF = "client.urls"
INSTALLED_APPS = []
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.middleware.common.CommonMiddleware"]
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request"]}}]
WSGI_APPLICATION = "client.wsgi.application"
USE_TZ = True
LANGUAGE_CODE = "ru-ru"
LOGGING = {"version":1,"disable_existing_loggers":False,"handlers":{"console":{"class":"logging.StreamHandler"}},"root":{"handlers":["console"],"level":"INFO"}}
