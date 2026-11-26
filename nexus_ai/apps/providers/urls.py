from fastapi import APIRouter
from fapix.core.router import register_urlpatterns
from fapix.router import DefaultRouter

from . import views


router = APIRouter(
    prefix="/providers",
    tags=["Providers"],
)

provider_models_router = DefaultRouter()
provider_models_router.register(
    "models",
    views.ProviderModelViewSet,
    basename="provider-model",
)

providers_router = DefaultRouter()
providers_router.register(
    "",
    views.ProviderViewSet,
    basename="provider",
)

# Register the static /models paths before /{name} provider detail paths.
urlpatterns = provider_models_router.generate_urlpatterns()
urlpatterns.extend(
    providers_router.generate_urlpatterns()
)

register_urlpatterns(
    router,
    urlpatterns,
)
