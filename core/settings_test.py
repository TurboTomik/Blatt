from .settings import *  # noqa: F403

# Test database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_db",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    }
}


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",  # Faster hashing
]


SECRET_KEY = "test-secret-key"  # noqa: S105
DEBUG = True
