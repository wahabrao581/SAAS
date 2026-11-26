
import uuid

from enum import Enum
from tortoise import fields, models


# ==========================================================
# ENUMS
# ==========================================================

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class AssetRole(str, Enum):
    FIRST_FRAME = "first_frame"
    LAST_FRAME = "last_frame"
    CHARACTER = "character"
    BACKGROUND = "background"
    REFERENCE = "reference"
    STYLE = "style"
    OTHER = "other"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    GENERATING = "generating"
    ASSEMBLING = "assembling"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELED = "canceled"


class ClipStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    GENERATING = "generating"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class AssetStorageProvider(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    R2 = "r2"
    GCS = "gcs"
    CUSTOM = "custom"


# ==========================================================
# VIDEO PROJECT
# ==========================================================

class VideoProject(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    user = fields.ForeignKeyField(
        "models.User",
        related_name="video_projects",
        on_delete=fields.CASCADE,
    )

    name = fields.CharField(
        max_length=255,
    )

    description = fields.TextField(
        null=True,
    )

    original_prompt = fields.TextField(
        null=True,
    )

    status = fields.CharField(
        max_length=30,
        default=ProjectStatus.DRAFT.value,
    )

    # Project-wide defaults.
    default_model = fields.CharField(
        max_length=100,
        null=True,
    )

    default_settings = fields.JSONField(
        default=dict,
    )

    # Final assembled video.
    final_video_url = fields.TextField(
        null=True,
    )

    final_video_storage_key = fields.TextField(
        null=True,
    )

    # Number of scenes.
    total_scenes = fields.IntField(
        default=0,
    )

    total_generated_clips = fields.IntField(
        default=0,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "video_projects"
        ordering = ["-created_at"]
        indexes = [
            ("user", "created_at"),
            ("user", "status"),
        ]

    def __str__(self):
        return self.name


# ==========================================================
# PROMPT SEGMENTS
# ==========================================================

class PromptSegment(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    project = fields.ForeignKeyField(
        "models.VideoProject",
        related_name="segments",
        on_delete=fields.CASCADE,
    )

    sequence = fields.IntField()

    prompt = fields.TextField()

    title = fields.CharField(
        max_length=255,
        null=True,
    )

    is_approved = fields.BooleanField(
        default=False,
    )

    metadata = fields.JSONField(
        default=dict,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "prompt_segments"
        unique_together = [
            ("project", "sequence"),
        ]
        ordering = ["sequence"]


# ==========================================================
# USER ASSETS
# ==========================================================

class Asset(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    user = fields.ForeignKeyField(
        "models.User",
        related_name="video_assets",
        on_delete=fields.CASCADE,
    )

    project = fields.ForeignKeyField(
        "models.VideoProject",
        related_name="assets",
        null=True,
        on_delete=fields.SET_NULL,
    )

    name = fields.CharField(
        max_length=255,
    )

    asset_type = fields.CharField(
        max_length=30,
        default=AssetType.IMAGE.value,
    )

    mime_type = fields.CharField(
        max_length=100,
    )

    file_size = fields.BigIntField(
        default=0,
    )

    storage_provider = fields.CharField(
        max_length=30,
        default=AssetStorageProvider.LOCAL.value,
    )

    storage_key = fields.TextField()

    # Public URL or temporary URL.
    # Prefer generating signed URLs at response time.
    url = fields.TextField(
        null=True,
    )

    checksum = fields.CharField(
        max_length=128,
        null=True,
    )

    width = fields.IntField(
        null=True,
    )

    height = fields.IntField(
        null=True,
    )

    duration = fields.FloatField(
        null=True,
    )

    metadata = fields.JSONField(
        default=dict,
    )

    is_deleted = fields.BooleanField(
        default=False,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    class Meta:
        table = "video_assets"
        ordering = ["-created_at"]
        indexes = [
            ("user", "created_at"),
            ("project", "created_at"),
        ]


# ==========================================================
# GENERATION JOB
# ==========================================================

class GenerationJob(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    user = fields.ForeignKeyField(
        "models.User",
        related_name="generation_jobs",
        on_delete=fields.CASCADE,
    )

    project = fields.ForeignKeyField(
        "models.VideoProject",
        related_name="generation_jobs",
        on_delete=fields.CASCADE,
    )

    status = fields.CharField(
        max_length=30,
        default=JobStatus.PENDING.value,
    )

    model_name = fields.CharField(
        max_length=100,
    )

    total_clips = fields.IntField(
        default=0,
    )

    completed_clips = fields.IntField(
        default=0,
    )

    failed_clips = fields.IntField(
        default=0,
    )

    # Estimated and reserved credits.
    estimated_credits = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    # Actual settled credits.
    actual_credits = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    # Subscription app reservation UUID.
    credit_reservation_id = fields.UUIDField(
        null=True,
    )

    idempotency_key = fields.CharField(
        max_length=255,
    )

    # Job-level generation options.
    settings = fields.JSONField(
        default=dict,
    )

    error_message = fields.TextField(
        null=True,
    )

    started_at = fields.DatetimeField(
        null=True,
    )

    completed_at = fields.DatetimeField(
        null=True,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "generation_jobs"
        unique_together = [
            ("user", "idempotency_key"),
        ]
        ordering = ["-created_at"]
        indexes = [
            ("user", "status"),
            ("project", "created_at"),
            ("status", "created_at"),
        ]


# ==========================================================
# VIDEO CLIPS
# ==========================================================

class VideoClip(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    project = fields.ForeignKeyField(
        "models.VideoProject",
        related_name="clips",
        on_delete=fields.CASCADE,
    )

    job = fields.ForeignKeyField(
        "models.GenerationJob",
        related_name="clips",
        on_delete=fields.CASCADE,
    )

    segment = fields.ForeignKeyField(
        "models.PromptSegment",
        related_name="clips",
        null=True,
        on_delete=fields.SET_NULL,
    )

    sequence = fields.IntField()

    prompt = fields.TextField()

    model_name = fields.CharField(
        max_length=100,
    )

    status = fields.CharField(
        max_length=30,
        default=ClipStatus.PENDING.value,
    )

    # Individual generation settings.
    settings = fields.JSONField(
        default=dict,
    )

    estimated_credits = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    actual_credits = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    # Remote GPU provider references.
    provider_name = fields.CharField(
        max_length=100,
        null=True,
    )

    provider_job_id = fields.CharField(
        max_length=255,
        null=True,
    )

    # Generated output.
    output_url = fields.TextField(
        null=True,
    )

    output_storage_key = fields.TextField(
        null=True,
    )

    output_duration = fields.FloatField(
        null=True,
    )

    output_width = fields.IntField(
        null=True,
    )

    output_height = fields.IntField(
        null=True,
    )

    progress = fields.IntField(
        default=0,
    )

    error_message = fields.TextField(
        null=True,
    )

    retry_count = fields.IntField(
        default=0,
    )

    started_at = fields.DatetimeField(
        null=True,
    )

    completed_at = fields.DatetimeField(
        null=True,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "video_clips"
        unique_together = [
            ("job", "sequence"),
        ]
        ordering = ["sequence"]
        indexes = [
            ("job", "status"),
            ("project", "sequence"),
        ]


# ==========================================================
# CLIP ASSET ASSOCIATION
# ==========================================================

class ClipAsset(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    clip = fields.ForeignKeyField(
        "models.VideoClip",
        related_name="asset_links",
        on_delete=fields.CASCADE,
    )

    asset = fields.ForeignKeyField(
        "models.Asset",
        related_name="clip_links",
        on_delete=fields.CASCADE,
    )

    role = fields.CharField(
        max_length=30,
    )

    sequence = fields.IntField(
        default=0,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    class Meta:
        table = "clip_assets"
        unique_together = [
            ("clip", "asset", "role"),
        ]
