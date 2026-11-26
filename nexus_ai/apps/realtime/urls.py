from . import views
from fastapi import APIRouter
from fapix.core.router import register_urlpatterns

router = APIRouter(prefix="/realtime", tags=["realtime"])

urlpatterns = [
    {
        "path": "/",
        "view": views.home,
        "method": "GET",
        "name": "home",
    },
]

register_urlpatterns(router, urlpatterns)
router.add_api_websocket_route(
    "/",
    views.RealtimeWebSocketView.handle_connection,
    name="realtime-websocket",
)
