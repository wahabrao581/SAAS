
from fastapi import APIRouter

from fapix.core.router import register_urlpatterns
from fapix.router import DefaultRouter

from . import views
from . import account_views


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)


# ==========================================================
# DEFAULT ROUTER
# ==========================================================

subscription_router = DefaultRouter()

subscription_router.register(
    "plans",
    views.SubscriptionPlanViewSet,
    basename="subscription-plan",
)


# ==========================================================
# URL PATTERNS
# ==========================================================

urlpatterns = []

urlpatterns.extend(
    subscription_router.generate_urlpatterns()
)

router.add_api_route("/me", account_views.account_overview, methods=["GET"])
router.add_api_route(
    "/available-plans",
    account_views.available_plans,
    methods=["GET"],
)
router.add_api_route(
    "/history",
    account_views.project_history,
    methods=["GET"],
)
router.add_api_route("/estimate", account_views.estimate_credits, methods=["POST"])
router.add_api_route(
    "/admin/users/{user_id}",
    account_views.admin_user_details,
    methods=["GET"],
)
router.add_api_route(
    "/admin/projects/{project_id}",
    account_views.admin_project_details,
    methods=["GET"],
)
router.add_api_route(
    "/admin/users/{user_id}/credits",
    account_views.admin_adjust_user_credits,
    methods=["POST"],
)
router.add_api_route(
    "/admin/users/{user_id}/models",
    account_views.admin_set_model_access,
    methods=["PUT"],
)
router.add_api_route(
    "/admin/users/{user_id}/subscription",
    account_views.admin_assign_subscription,
    methods=["POST"],
)
router.add_api_route(
    "/admin/payments/{payment_id}/confirm",
    account_views.admin_confirm_payment,
    methods=["POST"],
)

# ==========================================================
# REGISTER ROUTES
# ==========================================================

register_urlpatterns(
    router,
    urlpatterns,
)
