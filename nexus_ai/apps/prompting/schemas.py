
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ==========================================================
# COMMON
# ==========================================================

class APIResponse(BaseModel):

    success: bool = True

    message: str

    data: Any = None


# ==========================================================
# PROJECT
# ==========================================================

class ProjectCreateSchema(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=255,
    )

    description: str | None = None

    original_prompt: str | None = None

    default_model: str | None = None

    default_settings: dict = Field(
        default_factory=dict,
    )


class ProjectUpdateSchema(BaseModel):

    name: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = None

    default_model: str | None = None

    default_settings: dict | None = None


class ProjectReadSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    name: str

    description: str | None = None

    original_prompt: str | None = None

    status: str

    default_model: str | None = None

    default_settings: dict

    final_video_url: str | None = None

    total_scenes: int

    total_generated_clips: int

    created_at: datetime

    updated_at: datetime


# ==========================================================
# PROMPT SPLITTING
# ==========================================================

class PromptSplitSchema(BaseModel):

    project_id: UUID | None = None

    prompt: str = Field(
        min_length=1,
        max_length=100000,
    )

    separator_mode: Literal[
        "blank_lines",
        "numbered",
        "auto",
    ] = "auto"


class PromptSegmentReadSchema(BaseModel):

    id: UUID | None = None

    sequence: int

    title: str | None = None

    prompt: str

    is_approved: bool = False


class PromptSplitResponseSchema(BaseModel):

    total_segments: int

    segments: list[PromptSegmentReadSchema]


class PromptSegmentUpdateSchema(BaseModel):

    prompt: str = Field(
        min_length=1,
        max_length=20000,
    )

    title: str | None = None


class PromptApprovalSchema(BaseModel):

    segment_ids: list[UUID] = Field(
        min_length=1,
    )


# ==========================================================
# ASSETS
# ==========================================================

class AssetRegisterSchema(BaseModel):

    project_id: UUID | None = None

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    asset_type: Literal[
        "image",
        "video",
        "audio",
    ] = "image"

    mime_type: str

    file_size: int = Field(
        ge=1,
    )

    storage_provider: Literal[
        "local",
        "s3",
        "r2",
        "gcs",
        "custom",
    ]

    storage_key: str

    checksum: str | None = None

    width: int | None = Field(
        default=None,
        gt=0,
    )

    height: int | None = Field(
        default=None,
        gt=0,
    )

    metadata: dict = Field(
        default_factory=dict,
    )


class AssetReadSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    project_id: UUID | None = None

    name: str

    asset_type: str

    mime_type: str

    file_size: int

    storage_provider: str

    url: str | None = None

    checksum: str | None = None

    width: int | None = None

    height: int | None = None

    metadata: dict

    created_at: datetime


# ==========================================================
# CLIP ASSET REFERENCES
# ==========================================================

class ClipAssetInputSchema(BaseModel):

    asset_id: UUID

    role: Literal[
        "first_frame",
        "last_frame",
        "character",
        "background",
        "reference",
        "style",
        "other",
    ]

    sequence: int = Field(
        default=0,
        ge=0,
    )


# ==========================================================
# GENERATION SETTINGS
# ==========================================================

class GenerationSettingsSchema(BaseModel):

    resolution: Literal[
        "480p",
        "540p",
        "720p",
        "1080p",
        "1440p",
    ] = "720p"

    duration_seconds: float = Field(
        default=5,
        gt=0,
        le=60,
    )

    fps: int = Field(
        default=24,
        ge=1,
        le=120,
    )

    steps: int | None = Field(
        default=None,
        ge=1,
        le=200,
    )

    quality: Literal[
        "standard",
        "high",
        "ultra",
    ] = "standard"

    seed: int | None = None

    aspect_ratio: Literal[
        "16:9",
        "9:16",
        "1:1",
        "4:3",
        "3:4",
        "21:9",
    ] = "16:9"

    # Additional model-specific settings.
    extra: dict[str, Any] = Field(
        default_factory=dict,
    )


# ==========================================================
# CLIP SUBMISSION
# ==========================================================

class ClipCreateSchema(BaseModel):

    sequence: int = Field(
        ge=1,
    )

    segment_id: UUID | None = None

    prompt: str = Field(
        min_length=1,
        max_length=20000,
    )

    model_name: str = Field(
        min_length=1,
        max_length=100,
    )

    settings: GenerationSettingsSchema = Field(
        default_factory=GenerationSettingsSchema,
    )

    assets: list[ClipAssetInputSchema] = Field(
        default_factory=list,
        max_length=30,
    )


# ==========================================================
# GENERATION JOB SUBMISSION
# ==========================================================

class VideoGenerationSubmitSchema(BaseModel):

    project_id: UUID

    model_name: str

    clips: list[ClipCreateSchema] = Field(
        min_length=1,
        max_length=100,
    )

    idempotency_key: str = Field(
        min_length=8,
        max_length=255,
    )

    # Job-level settings.
    settings: dict = Field(
        default_factory=dict,
    )

    @field_validator("clips")
    @classmethod
    def validate_sequences(cls, clips):

        sequences = [
            clip.sequence
            for clip in clips
        ]

        if len(sequences) != len(set(sequences)):
            raise ValueError(
                "Clip sequence numbers must be unique."
            )

        return clips


class VideoGenerationSubmitResponseSchema(BaseModel):

    job_id: UUID

    project_id: UUID

    status: str

    total_clips: int

    estimated_credits: Decimal

    message: str


# ==========================================================
# CLIP RESPONSE
# ==========================================================

class VideoClipReadSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    project_id: UUID

    job_id: UUID

    segment_id: UUID | None = None

    sequence: int

    prompt: str

    model_name: str

    status: str

    settings: dict

    estimated_credits: Decimal

    actual_credits: Decimal

    output_url: str | None = None

    output_duration: float | None = None

    progress: int

    error_message: str | None = None

    created_at: datetime

    completed_at: datetime | None = None


# ==========================================================
# GENERATION JOB RESPONSE
# ==========================================================

class GenerationJobReadSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    project_id: UUID

    status: str

    model_name: str

    total_clips: int

    completed_clips: int

    failed_clips: int

    estimated_credits: Decimal

    actual_credits: Decimal

    error_message: str | None = None

    started_at: datetime | None = None

    completed_at: datetime | None = None

    created_at: datetime


# ==========================================================
# JOB STATUS REQUEST
# ==========================================================

class JobStatusRequestSchema(BaseModel):

    job_id: UUID


# ==========================================================
# CANCEL JOB
# ==========================================================

class JobCancelSchema(BaseModel):

    job_id: UUID

    reason: str | None = None


# ==========================================================
# JOIN VIDEO CLIPS
# ==========================================================

class VideoAssemblySchema(BaseModel):

    project_id: UUID

    job_id: UUID

    clip_ids: list[UUID] | None = None

    output_name: str = Field(
        default="final_video.mp4",
        max_length=255,
    )

    include_audio: bool = True


class VideoAssemblyResponseSchema(BaseModel):

    project_id: UUID

    job_id: UUID

    status: str

    message: str


# ==========================================================
# ASSET DELETE
# ==========================================================

class AssetDeleteSchema(BaseModel):

    asset_id: UUID


# ==========================================================
# ADMIN
# ==========================================================

class AdminJobRetrySchema(BaseModel):

    job_id: UUID

    failed_only: bool = True


class AdminJobStatusUpdateSchema(BaseModel):

    status: Literal[
        "pending",
        "queued",
        "processing",
        "failed",
        "canceled",
    ]

    reason: str | None = None
