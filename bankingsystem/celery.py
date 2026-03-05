# celery.py
from __future__ import absolute_import
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bankingsystem.settings')

# Create Celery app
app = Celery('bankingsystem')

# Load task modules from all registered Django apps
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
