from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.responses import HTMLResponse
from .schemas import (
    UserCreate,
    UserRead,
    LoginSchema,
    TokenResponse,
    RefreshTokenSchema,
)

from .views import (
    signup_user,
    login_user,
    refresh_access_token,
   
)
from . import viewsets
from fapix.core.router import register_urlpatterns
from fapix.router import DefaultRouter


router = APIRouter(
    prefix="/user",
    tags=["Authentication"],
)

# HTTP CRUD For Users
user_router = DefaultRouter()


user_router.register("", viewsets.UserViewSet, basename="user")
urlpatterns = [
    # Custom / Manual views
]

# 3. Extend with automatically generated ViewSet patterns
urlpatterns.extend(user_router.generate_urlpatterns())

# 4. Register patterns onto router
register_urlpatterns(router, urlpatterns)


# # ==========================================================
# # SIGNUP
# # ==========================================================

@router.post(
    "/signup",
    response_model=UserRead,
)
async def signup(
    data: UserCreate,
):

    return await signup_user(
        data
    )


# ==========================================================
# LOGIN
# ==========================================================
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
)
async def login(data: LoginSchema):
    # Call your original login_user logic (handles password verification & token generation)
    tokens = await login_user(data)
    from apps.auth.models import User
    user = await User.get(email=data.email)

    # Return combined dictionary matching TokenResponse schema
    return {
        **tokens,
        "user_id": user.id,
        "username": user.username or user.email.split("@")[0],
        "email": user.email,
        "role": getattr(user, "role", "user"),
        "full_name": getattr(user, "full_name", None),
        "avatar_url": getattr(user, "avatar_url", None),
        "is_staff": getattr(user, "is_staff", False),
    }
# ==========================================================
# REFRESH
# ==========================================================

@router.post(
    "/refresh",
)
async def refresh_token(
    data: RefreshTokenSchema,
):

    return await refresh_access_token(
        data
    )
