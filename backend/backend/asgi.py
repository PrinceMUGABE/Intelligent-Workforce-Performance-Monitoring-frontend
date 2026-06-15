# asgi.py

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

websocket_urlpatterns = []

# Only import routing if the apps exist
try:
    from chatApp import routing as chat_routing
    websocket_urlpatterns += chat_routing.websocket_urlpatterns
except (ImportError, AttributeError) as e:
    print(f"chatApp routing not loaded: {e}")

try:
    from assistanceApp import routing as assistance_routing
    websocket_urlpatterns += assistance_routing.websocket_urlpatterns
except (ImportError, AttributeError) as e:
    print(f"assistanceApp routing not loaded: {e}")

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})