
from fastapi import APIRouter


# Prompting user operations are dispatched through
# the single central WebSocket connection owned by
# apps.realtime.urls.

router = APIRouter(
    prefix="/prompting",
    tags=["Prompting"],
)

# No HTTP endpoints are registered here.
# Do not mount a second WebSocket endpoint here.
urlpatterns = []
