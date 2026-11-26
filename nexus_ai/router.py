from importlib import import_module
from pathlib import Path

from fastapi import APIRouter

from fapix.core.homepage import router as _fapix_homepage_router
from apps.auth.urls import router as auth_router
from apps.realtime.urls import router as realtime_router
from apps.providers.urls import router as providers_router
from apps.subscriptions.urls import router as subscriptions_router
from apps.prompting.urls import router as prompting_router
from apps.frontend.urls import router as frontend_router


router = APIRouter()







router.include_router(auth_router)

router.include_router(realtime_router)

router.include_router(providers_router)

router.include_router(subscriptions_router)


router.include_router(prompting_router)
router.include_router(frontend_router)
