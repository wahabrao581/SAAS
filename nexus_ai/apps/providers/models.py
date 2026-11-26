import uuid
from enum import Enum

from tortoise import fields, models


class ProviderType(str, Enum):
    VIDEO_GENERATION = "video_generation"
    PAYMENT = "payment"
    STORAGE = "storage"
    OTHER = "other"


class Provider(models.Model):
    """External service configuration shared by the application."""

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    # Stable identifier used by payments and generated clips.
    name = fields.CharField(
        max_length=100,
        unique=True,
    )

    display_name = fields.CharField(
        max_length=150,
    )

    provider_type = fields.CharField(
        max_length=30,
        default=ProviderType.OTHER.value,
    )

    base_url = fields.TextField(
        null=True,
    )

    # Store the environment variable name, never the credential itself.
    api_key_env = fields.CharField(
        max_length=100,
        null=True,
    )

    is_active = fields.BooleanField(
        default=True,
    )

    settings = fields.JSONField(
        default=dict,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "providers"
        ordering = ["name"]
        indexes = [
            ("provider_type", "is_active"),
        ]

    def __str__(self):
        return self.display_name


class ProviderModel(models.Model):
    """A model exposed by a video-generation provider."""

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    provider = fields.ForeignKeyField(
        "models.Provider",
        related_name="models",
        on_delete=fields.CASCADE,
    )

    # Matches model_name used by generation requests and pricing config.
    name = fields.CharField(
        max_length=100,
    )

    display_name = fields.CharField(
        max_length=150,
    )

    description = fields.TextField(
        null=True,
    )

    capabilities = fields.JSONField(
        default=dict,
    )

    is_active = fields.BooleanField(
        default=True,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "provider_models"
        unique_together = [
            ("provider", "name"),
        ]
        ordering = ["provider_id", "name"]
        indexes = [
            ("provider", "is_active"),
        ]

    def __str__(self):
        return self.name
