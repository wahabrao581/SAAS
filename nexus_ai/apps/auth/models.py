
import uuid
from enum import Enum

from tortoise import fields, models


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class User(models.Model):
    """
    Main SaaS user model.

    Authentication, account status, profile information,
    administrative access and account lifecycle.
    """

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    # Identity
    email = fields.CharField(
        max_length=255,
        unique=True,
    )

    username = fields.CharField(
        max_length=150,
        unique=True,
        null=True,
    )

    full_name = fields.CharField(
        max_length=255,
        null=True,
    )

    avatar_url = fields.TextField(
        null=True,
    )

    # Authentication
    hashed_password = fields.CharField(
        max_length=255,
    )

    is_active = fields.BooleanField(
        default=True,
    )

    is_verified = fields.BooleanField(
        default=False,
    )

    # Authorization
    role = fields.CharField(
        max_length=50,
        default=UserRole.USER.value,
    )

    # None means all configured models are allowed; a list is an allowlist.
    allowed_models = fields.JSONField(
        null=True,
        default=None,
    )

    # Account security
    last_login_at = fields.DatetimeField(
        null=True,
    )

    password_changed_at = fields.DatetimeField(
        null=True,
    )

    failed_login_attempts = fields.IntField(
        default=0,
    )

    locked_until = fields.DatetimeField(
        null=True,
    )

    # Account lifecycle
    deactivated_at = fields.DatetimeField(
        null=True,
    )

    deleted_at = fields.DatetimeField(
        null=True,
    )

    # Optional onboarding tracking
    onboarding_completed = fields.BooleanField(
        default=False,
    )

    # Timestamps
    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "auth_users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role in (
            UserRole.ADMIN.value,
            UserRole.SUPERUSER.value,
        )

    @property
    def is_superuser(self):
        return self.role == UserRole.SUPERUSER.value
