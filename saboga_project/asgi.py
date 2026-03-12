"""
ASGI config for saboga_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# no custom ASGI instrumentation now; django_prometheus handles
# metrics via middleware configured in settings.  we still import the
# module so that the gauge object is available to any test that needs it.
from api import instrumentation  # noqa: F401

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saboga_project.settings")

# create the standard Django ASGI application first
application = get_asgi_application()

# django_prometheus middleware configured in settings will expose
# `/metrics` automatically; no further wrapping is necessary.
