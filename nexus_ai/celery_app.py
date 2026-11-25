
import os

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown


# ==========================================================
# ENVIRONMENT
# ==========================================================

os.environ.setdefault(
    "APP_SETTINGS_MODULE",
    "config.settings",
)


# ==========================================================
# CELERY APPLICATION
# ==========================================================

app = Celery(
    "video_saas",
)


# ==========================================================
# CONFIGURATION
# ==========================================================

app.conf.update(

    broker_url=os.getenv(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/1",
    ),

    result_backend=os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/2",
    ),

    task_serializer="json",

    result_serializer="json",

    accept_content=[
        "json",
    ],

    timezone="UTC",

    enable_utc=True,

    task_track_started=True,

    task_acks_late=True,

    worker_prefetch_multiplier=1,

    task_reject_on_worker_lost=True,

    broker_connection_retry_on_startup=True,

    task_default_queue="default",

    task_routes={

        # Prompting tasks
        "prompting.*": {
            "queue": "prompting",
        },

        # Provider / GPU tasks
        "providers.*": {
            "queue": "providers",
        },

        # Subscription tasks
        "subscriptions.*": {
            "queue": "subscriptions",
        },

        # Authentication tasks
        "auth.*": {
            "queue": "auth",
        },
    },

    # Discover tasks from installed applications.
    imports=(
        
        "apps.subscriptions.celery",
        
        "apps.prompting.celery",
        
    ),

)


# ==========================================================
# AUTO DISCOVERY
# ==========================================================

app.autodiscover_tasks(
    [
        
        "apps.subscriptions",
        
        "apps.prompting",
        
    ],
    related_name="celery",
    force=True,
)


# ==========================================================
# WORKER INITIALIZATION
# ==========================================================

@worker_process_init.connect
def worker_init(**kwargs):

    print(
        "[CELERY] Worker process initialized."
    )


@worker_process_shutdown.connect
def worker_shutdown(**kwargs):

    print(
        "[CELERY] Worker process shutting down."
    )


# ==========================================================
# DEBUG TASK
# ==========================================================

@app.task(
    bind=True,
    name="core.debug_task",
)
def debug_task(self):

    print(
        f"Celery request: {self.request!r}"
    )

    return {
        "status": "success",
        "message": "Root Celery application is working.",
    }
