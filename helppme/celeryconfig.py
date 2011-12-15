BROKER_URL = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = "localhost"
CELERY_REDIS_PORT = 6379
CELERY_REDIS_DB = 1
CELERY_IMPORTS = ("helppme.views.user", "helppme.celery_tasks")
CELERY_DISABLE_RATE_LIMITS = True