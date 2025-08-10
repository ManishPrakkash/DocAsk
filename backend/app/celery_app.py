from celery import Celery
from decouple import config
import logging

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = config('REDIS_URL', default='redis://:redis_secure_password@localhost:6379/0')

# Create Celery instance
celery_app = Celery(
    'clausewise',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
    task_track_started=True,
    task_always_eager=False,  # Set to True for testing without Redis
    worker_prefetch_multiplier=1,  # Disable prefetching for better resource management
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks to prevent memory leaks
)

# Configure logging
celery_app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
celery_app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Task routing (optional)
celery_app.conf.task_routes = {
    'app.tasks.process_document': {'queue': 'document_processing'},
    'app.tasks.analyze_document': {'queue': 'analysis'},
}

if __name__ == '__main__':
    celery_app.start()