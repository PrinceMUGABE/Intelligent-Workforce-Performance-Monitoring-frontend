# Save as debug.py in backend/ directory
import sys
import os
import django

print("Python path:", sys.path)
print("Django version:", django.get_version())
print("Current directory:", os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
print("INSTALLED_APPS:", settings.INSTALLED_APPS)
print("DATABASES:", settings.DATABASES)