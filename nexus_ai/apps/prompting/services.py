import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from tortoise.transactions import in_transaction

from apps.auth.models import User
from .config import get_model_credit_rate
from .models import (
    Asset,
    ClipAsset,
    ClipStatus,
    GenerationJob,
    JobStatus,
    ProjectStatus,
    PromptSegment,
    VideoClip,
    VideoProject,
)


class ProjectNotFound(LookupError):
    pass


class PromptSegmentNotFound(LookupError):
    pass


class AssetNotFound(LookupError):
    pass


class JobNotFound(LookupError):
    pass


class IdempotencyConflict(ValueError):
    pass


def _validate_page(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or offset < 0:
        raise ValueError("limit must be positive and offset cannot be negative.")
    return min(limit, 100), offset


async def _owned_project(user_id: UUID, project_id: UUID) -> VideoProject:
    project = await VideoProject.get_or_none(
        id=project_id,
        user_id=user_id,
    )
    if project is None:
        raise ProjectNotFound("Project not found.")
    return project


async def create_project(user_id: UUID, data) -> VideoProject:
    return await VideoProject.create(
        user_id=user_id,
        name=data.name,
        description=data.description,
        original_prompt=data.original_prompt,
        default_model=data.default_model,
        default_settings=data.default_settings,
    )


async def get_projects(
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> list[VideoProject]:
    limit, offset = _validate_page(limit, offset)
    return await VideoProject.filter(
        user_id=user_id,
    ).offset(offset).limit(limit)


async def get_project(user_id: UUID, project_id: UUID) -> VideoProject:
    return await _owned_project(user_id, project_id)


async def update_project(
    user_id: UUID,
    project_id: UUID,
    data,
) -> VideoProject:
    project = await _owned_project(user_id, project_id)
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)
    if updates:
        await project.save(update_fields=[*updates, "updated_at"])
    return project


async def archive_project(
    user_id: UUID,
    project_id: UUID,
) -> VideoProject:
    project = await _owned_project(user_id, project_id)
    project.status = ProjectStatus.ARCHIVED.value
    await project.save(update_fields=["status", "updated_at"])
    return project


def _split_prompt(prompt: str, separator_mode: str) -> list[str]:
    text = prompt.strip()
    if not text:
        raise ValueError("Prompt cannot be empty.")

    numbered_marker = re.compile(
        r"(?m)^\s*(?:(?:scene|shot)\s*)?\d+\s*[.):\-]\s*",
        re.IGNORECASE,
    )
    numbered_parts = numbered_marker.split(text)
    has_numbered_markers = len(numbered_parts) > 1

    if separator_mode == "numbered":
        parts = numbered_parts if has_numbered_markers else [text]
    elif separator_mode == "blank_lines":
        parts = re.split(r"\n\s*\n+", text)
    elif separator_mode == "auto":
        if has_numbered_markers:
            parts = numbered_parts
        else:
            parts = re.split(r"\n\s*\n+", text)
    else:
        raise ValueError("Unsupported prompt separator mode.")

    segments = [part.strip() for part in parts if part.strip()]
    return segments or [text]


async def split_and_save_prompt(
    user_id: UUID,
    prompt: str,
    project_id: UUID | None,
    separator_mode: str,
) -> dict:
    segments_text = _split_prompt(prompt, separator_mode)

    async with in_transaction() as connection:
        if project_id is None:
            project = await VideoProject.create(
                user_id=user_id,
                name=prompt.strip().splitlines()[0][:255],
                original_prompt=prompt,
                status=ProjectStatus.DRAFT.value,
                using_db=connection,
            )
        else:
            project = await VideoProject.filter(
                id=project_id,
                user_id=user_id,
            ).using_db(connection).select_for_update().get_or_none()
            if project is None:
                raise ProjectNotFound("Project not found.")
            if project.status in (
                ProjectStatus.GENERATING.value,
                ProjectStatus.COMPLETED.value,
                ProjectStatus.ARCHIVED.value,
            ):
                raise ValueError("This project cannot be edited in its current state.")
            project.original_prompt = prompt
            project.status = ProjectStatus.DRAFT.value
            await project.save(
                using_db=connection,
                update_fields=["original_prompt", "status", "updated_at"],
            )
            await PromptSegment.filter(
                project_id=project.id,
            ).using_db(connection).delete()

        created_segments = []
        for sequence, segment_prompt in enumerate(segments_text, start=1):
            title = segment_prompt.splitlines()[0].strip()[:255] or None
            created_segments.append(
                await PromptSegment.create(
                    project_id=project.id,
                    sequence=sequence,
                    prompt=segment_prompt,
                    title=title,
                    using_db=connection,
                )
            )

        project.total_scenes = len(created_segments)
        await project.save(
            using_db=connection,
            update_fields=["total_scenes", "updated_at"],
        )

    return {"project": project, "segments": created_segments}


async def get_prompt_segments(
    user_id: UUID,
    project_id: UUID,
) -> list[PromptSegment]:
    await _owned_project(user_id, project_id)
    return await PromptSegment.filter(
        project_id=project_id,
    ).order_by("sequence")


async def update_prompt_segment(
    user_id: UUID,
    segment_id: UUID,
    data,
) -> PromptSegment:
    segment = await PromptSegment.filter(
        id=segment_id,
        project__user_id=user_id,
    ).first()
    if segment is None:
        raise PromptSegmentNotFound("Prompt segment not found.")

    segment.prompt = data.prompt
    segment.title = data.title
    segment.is_approved = False
    await segment.save(
        update_fields=["prompt", "title", "is_approved", "updated_at"],
    )
    return segment


async def approve_prompt_segments(
    user_id: UUID,
    segment_ids: list[UUID],
) -> list[PromptSegment]:
    if len(segment_ids) != len(set(segment_ids)):
        raise ValueError("Segment IDs must be unique.")

    segments = await PromptSegment.filter(
        id__in=segment_ids,
        project__user_id=user_id,
    )
    if len(segments) != len(segment_ids):
        raise PromptSegmentNotFound("One or more prompt segments were not found.")

    for segment in segments:
        segment.is_approved = True
        await segment.save(update_fields=["is_approved", "updated_at"])
    return segments


async def register_asset(user_id: UUID, data) -> Asset:
    if data.project_id is not None:
        await _owned_project(user_id, data.project_id)
    if not data.storage_key.strip():
        raise ValueError("Asset storage_key cannot be empty.")

    return await Asset.create(
        user_id=user_id,
        project_id=data.project_id,
        name=data.name,
        asset_type=data.asset_type,
        mime_type=data.mime_type,
        file_size=data.file_size,
        storage_provider=data.storage_provider,
        storage_key=data.storage_key,
        checksum=data.checksum,
        width=data.width,
        height=data.height,
        metadata=data.metadata,
    )


async def get_project_assets(
    user_id: UUID,
    project_id: UUID,
) -> list[Asset]:
    await _owned_project(user_id, project_id)
    return await Asset.filter(
        project_id=project_id,
        user_id=user_id,
        is_deleted=False,
    ).order_by("-created_at")


async def delete_asset(user_id: UUID, asset_id: UUID) -> Asset:
    asset = await Asset.get_or_none(
        id=asset_id,
        user_id=user_id,
        is_deleted=False,
    )
    if asset is None:
        raise AssetNotFound("Asset not found.")
    asset.is_deleted = True
    await asset.save(update_fields=["is_deleted"])
    return asset


async def _clip_credit_estimate(
    model_name: str,
    duration_seconds: float,
    quality: str,
) -> Decimal:
    rate = await get_model_credit_rate(model_name, quality)
    return (rate * Decimal(str(duration_seconds))).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


async def _require_model_access(user_id: UUID, model_name: str) -> None:
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise ValueError("User account was not found.")
    if user.allowed_models is not None and model_name not in user.allowed_models:
        raise ValueError(f"Your account does not have access to model {model_name!r}.")


async def _existing_job_for_key(
    user_id: UUID,
    idempotency_key: str,
) -> GenerationJob | None:
    return await GenerationJob.filter(
        user_id=user_id,
        idempotency_key=idempotency_key,
    ).first()


async def submit_generation_job(user_id: UUID, data) -> GenerationJob:
    project = await _owned_project(user_id, data.project_id)
    if project.status == ProjectStatus.ARCHIVED.value:
        raise ValueError("Archived projects cannot start generation.")

    model_names = {data.model_name, *(clip.model_name for clip in data.clips)}
    for model_name in model_names:
        await _require_model_access(user_id, model_name)

    existing = await _existing_job_for_key(user_id, data.idempotency_key)
    if existing is not None:
        if (
            existing.project_id != data.project_id
            or existing.model_name != data.model_name
            or existing.total_clips != len(data.clips)
        ):
            raise IdempotencyConflict(
                "Idempotency key was already used for a different generation request."
            )
        return existing

    segment_ids = {
        clip.segment_id for clip in data.clips if clip.segment_id is not None
    }
    if segment_ids:
        owned_segments = await PromptSegment.filter(
            id__in=segment_ids,
            project_id=project.id,
            is_approved=True,
        )
        if len(owned_segments) != len(segment_ids):
            raise ValueError(
                "Every referenced prompt segment must belong to this project and be approved."
            )

    asset_ids = {
        asset.asset_id for clip in data.clips for asset in clip.assets
    }
    assets_by_id = {}
    if asset_ids:
        assets = await Asset.filter(
            id__in=asset_ids,
            user_id=user_id,
            is_deleted=False,
        )
        assets_by_id = {asset.id: asset for asset in assets}
        if len(assets_by_id) != len(asset_ids):
            raise AssetNotFound("One or more referenced assets were not found.")
        if any(
            asset.project_id not in (None, project.id)
            for asset in assets_by_id.values()
        ):
            raise AssetNotFound("An asset is not available to this project.")

    estimates = []
    for clip in data.clips:
        estimates.append(await _clip_credit_estimate(
            clip.model_name,
            clip.settings.duration_seconds,
            clip.settings.quality,
        ))
    estimated_credits = sum(estimates, Decimal("0"))

    try:
        async with in_transaction() as connection:
            existing = await GenerationJob.filter(
                user_id=user_id,
                idempotency_key=data.idempotency_key,
            ).using_db(connection).first()
            if existing is not None:
                return existing

            job = await GenerationJob.create(
                user_id=user_id,
                project_id=project.id,
                status=JobStatus.PENDING.value,
                model_name=data.model_name,
                total_clips=len(data.clips),
                estimated_credits=estimated_credits,
                idempotency_key=data.idempotency_key,
                settings=data.settings,
                using_db=connection,
            )

            for clip_data, estimate in zip(data.clips, estimates):
                settings = clip_data.settings.model_dump(mode="json")
                clip = await VideoClip.create(
                    project_id=project.id,
                    job_id=job.id,
                    segment_id=clip_data.segment_id,
                    sequence=clip_data.sequence,
                    prompt=clip_data.prompt,
                    model_name=data.model_name,
                    status=ClipStatus.PENDING.value,
                    settings=settings,
                    estimated_credits=estimate,
                    using_db=connection,
                )
                for asset_data in clip_data.assets:
                    await ClipAsset.create(
                        clip_id=clip.id,
                        asset_id=assets_by_id[asset_data.asset_id].id,
                        role=asset_data.role,
                        sequence=asset_data.sequence,
                        using_db=connection,
                    )
    except Exception:
        concurrent_job = await _existing_job_for_key(
            user_id,
            data.idempotency_key,
        )
        if concurrent_job is not None:
            return concurrent_job
        raise

    from apps.subscriptions.services import reserve_credits

    try:
        reservation = await reserve_credits(
            user_id=user_id,
            amount=estimated_credits,
            reference_id=str(job.id),
            idempotency_key=f"generation:{job.id}",
            metadata={"project_id": str(project.id)},
        )
    except Exception:
        await job.delete()
        raise

    job.credit_reservation_id = reservation.id
    job.status = JobStatus.QUEUED.value
    await job.save(
        update_fields=["credit_reservation_id", "status", "updated_at"],
    )

    project.status = ProjectStatus.GENERATING.value
    await project.save(update_fields=["status", "updated_at"])

    try:
        from .celery import process_generation_job

        process_generation_job.delay(str(job.id))
    except Exception:
        from apps.subscriptions.services import release_reservation

        await release_reservation(
            reservation.id,
            reason="Generation task could not be queued",
        )
        job.status = JobStatus.FAILED.value
        job.error_message = "Generation task could not be queued."
        job.completed_at = datetime.now(timezone.utc)
        await job.save(
            update_fields=[
                "status",
                "error_message",
                "completed_at",
                "updated_at",
            ],
        )
        raise

    return job


async def get_generation_job(
    user_id: UUID,
    job_id: UUID,
) -> GenerationJob:
    job = await GenerationJob.get_or_none(
        id=job_id,
        user_id=user_id,
    )
    if job is None:
        raise JobNotFound("Generation job not found.")
    return job


async def get_job_clips(
    user_id: UUID,
    job_id: UUID,
) -> list[VideoClip]:
    await get_generation_job(user_id, job_id)
    return await VideoClip.filter(
        job_id=job_id,
    ).order_by("sequence")


async def cancel_generation_job(
    user_id: UUID,
    job_id: UUID,
) -> GenerationJob:
    job = await get_generation_job(user_id, job_id)
    if job.status in (
        JobStatus.COMPLETED.value,
        JobStatus.PARTIAL.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELED.value,
    ):
        return job

    if job.credit_reservation_id is not None:
        from apps.subscriptions.models import (
            CreditReservation,
            CreditReservationStatus,
        )
        from apps.subscriptions.services import release_reservation

        reservation = await CreditReservation.get_or_none(
            id=job.credit_reservation_id,
        )
        if (
            reservation is not None
            and reservation.status == CreditReservationStatus.RESERVED.value
        ):
            await release_reservation(
                reservation.id,
                reason="Generation job canceled",
            )

    now = datetime.now(timezone.utc)
    job.status = JobStatus.CANCELED.value
    job.completed_at = now
    await job.save(
        update_fields=["status", "completed_at", "updated_at"],
    )
    await VideoClip.filter(
        job_id=job.id,
        status__in=[
            ClipStatus.PENDING.value,
            ClipStatus.QUEUED.value,
        ],
    ).update(
        status=ClipStatus.CANCELED.value,
        completed_at=now,
    )
    return job


async def request_video_assembly(
    user_id: UUID,
    job_id: UUID,
    project_id: UUID | None = None,
    clip_ids: list[UUID] | None = None,
) -> GenerationJob:
    job = await get_generation_job(user_id, job_id)
    if project_id is not None and job.project_id != project_id:
        raise JobNotFound("Generation job not found.")
    if job.status in (JobStatus.CANCELED.value, JobStatus.FAILED.value):
        raise ValueError("This generation job cannot be assembled.")

    completed_clips = VideoClip.filter(
        job_id=job.id,
        status=ClipStatus.COMPLETED.value,
    )
    if clip_ids is not None:
        if not clip_ids or len(clip_ids) != len(set(clip_ids)):
            raise ValueError("clip_ids must contain unique clip IDs.")
        completed_clips = completed_clips.filter(id__in=clip_ids)
    clips = await completed_clips.order_by("sequence")
    if not clips:
        raise ValueError("No completed clips are available for assembly.")
    if clip_ids is not None and len(clips) != len(clip_ids):
        raise ValueError("One or more selected clips are unavailable.")

    from .celery import assemble_video_task

    job.status = JobStatus.ASSEMBLING.value
    await job.save(update_fields=["status", "updated_at"])
    try:
        assemble_video_task.delay(
            str(job.id),
            [str(clip.id) for clip in clips],
        )
    except Exception:
        job.status = JobStatus.PROCESSING.value
        await job.save(update_fields=["status", "updated_at"])
        raise
    return job


async def complete_video_assembly(
    job_id: UUID,
    output_url: str | None,
    storage_key: str,
) -> VideoProject:
    job = await GenerationJob.get_or_none(id=job_id)
    if job is None:
        raise JobNotFound("Generation job not found.")

    if job.credit_reservation_id is not None:
        from apps.subscriptions.services import consume_reservation

        await consume_reservation(job.credit_reservation_id)

    async with in_transaction() as connection:
        project = await VideoProject.filter(
            id=job.project_id,
        ).using_db(connection).select_for_update().get_or_none()
        locked_job = await GenerationJob.filter(
            id=job.id,
        ).using_db(connection).select_for_update().get_or_none()
        if project is None or locked_job is None:
            raise JobNotFound("Generation job or project not found.")
        if locked_job.status == JobStatus.CANCELED.value:
            raise ValueError("Canceled jobs cannot complete assembly.")

        now = datetime.now(timezone.utc)
        project.final_video_url = output_url
        project.final_video_storage_key = storage_key
        project.status = ProjectStatus.COMPLETED.value
        project.total_generated_clips = await VideoClip.filter(
            job_id=locked_job.id,
            status=ClipStatus.COMPLETED.value,
        ).using_db(connection).count()
        await project.save(
            using_db=connection,
            update_fields=[
                "final_video_url",
                "final_video_storage_key",
                "status",
                "total_generated_clips",
                "updated_at",
            ],
        )

        locked_job.status = JobStatus.COMPLETED.value
        locked_job.actual_credits = locked_job.estimated_credits
        locked_job.completed_at = now
        await locked_job.save(
            using_db=connection,
            update_fields=[
                "status",
                "actual_credits",
                "completed_at",
                "updated_at",
            ],
        )
        return project
