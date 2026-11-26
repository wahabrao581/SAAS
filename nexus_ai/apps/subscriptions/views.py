
from fapix.views import ModelViewSet

from apps.auth.permissions import IsSuperUser

from .models import SubscriptionPlan

from .schemas import (
    SubscriptionPlanRead,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
)


class SubscriptionPlanViewSet(ModelViewSet):
    """
    Administrative subscription plan management.
    """

    model = SubscriptionPlan

    schema = SubscriptionPlanRead

    action_schemas = {
        "create": SubscriptionPlanCreate,
        "update": SubscriptionPlanUpdate,
    }

    # Only superusers can manage subscription plans.
    permission_classes = [IsSuperUser]

    action_permissions = {
        "list": [IsSuperUser],
        "retrieve": [IsSuperUser],
        "create": [IsSuperUser],
        "update": [IsSuperUser],
        "partial_update": [IsSuperUser],
        "destroy": [IsSuperUser],
    }

    lookup_fields = ["slug"]

    search_fields = [
        "name",
        "slug",
        "description",
    ]

    filterset_fields = [
        "is_active",
        "is_public",
        "billing_interval",
        "currency",
    ]

    ordering_fields = [
        "price",
        "credits_per_period",
        "created_at",
    ]

    default_ordering = ["price"]
