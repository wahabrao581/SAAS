from fapix.views import ModelViewSet

from apps.auth.permissions import IsSuperUser

from .models import Provider, ProviderModel
from .schemas import (
    ProviderCreate,
    ProviderModelCreate,
    ProviderModelRead,
    ProviderModelUpdate,
    ProviderRead,
    ProviderUpdate,
)


class ProviderViewSet(ModelViewSet):
    """Superuser management of external service providers."""

    model = Provider
    schema = ProviderRead

    action_schemas = {
        "create": ProviderCreate,
        "update": ProviderUpdate,
    }

    permission_classes = [IsSuperUser]
    action_permissions = {
        "list": [IsSuperUser],
        "retrieve": [IsSuperUser],
        "create": [IsSuperUser],
        "update": [IsSuperUser],
        "partial_update": [IsSuperUser],
        "destroy": [IsSuperUser],
    }

    lookup_fields = ["name"]
    search_fields = ["name", "display_name"]
    filterset_fields = ["provider_type", "is_active"]
    ordering_fields = ["name", "display_name", "created_at"]
    default_ordering = ["name"]


class ProviderModelViewSet(ModelViewSet):
    """Superuser management of models offered by providers."""

    model = ProviderModel
    schema = ProviderModelRead

    action_schemas = {
        "create": ProviderModelCreate,
        "update": ProviderModelUpdate,
    }

    permission_classes = [IsSuperUser]
    action_permissions = {
        "list": [IsSuperUser],
        "retrieve": [IsSuperUser],
        "create": [IsSuperUser],
        "update": [IsSuperUser],
        "partial_update": [IsSuperUser],
        "destroy": [IsSuperUser],
    }

    lookup_fields = ["id"]
    search_fields = ["name", "display_name", "description"]
    filterset_fields = ["provider_id", "is_active"]
    ordering_fields = ["name", "display_name", "created_at"]
    default_ordering = ["provider_id", "name"]
