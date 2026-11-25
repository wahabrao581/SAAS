from fastapi import Request, WebSocket
from fapix.viewsets.websocket import WebSocketApiView

from apps.auth.permissions import IsAuthenticated
from apps.prompting.views import PromptingActionMixin


class RealtimeWebSocketView(
    PromptingActionMixin,
    WebSocketApiView,
):
    """Authenticated WebSocket endpoint for prompting and generation actions."""

    action_permissions = {
        **PromptingActionMixin.action_permissions,
        "ws_connect": [IsAuthenticated],
    }

    async def authenticate_websocket(
        self,
        websocket: WebSocket,
        token: str | None,
    ) -> bool:
        authenticated = await super().authenticate_websocket(websocket, token)
        if authenticated:
            self.user = websocket.state.user
        return authenticated


async def home(
    request: Request,
):

    return {
        "message": "Hello from the Fapix!"
    }
