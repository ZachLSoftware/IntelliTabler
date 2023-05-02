import os
from celery import Celery

"""
Create base celery settings
"""
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IntelliTabler.settings")
app = Celery("IntelliTabler")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
