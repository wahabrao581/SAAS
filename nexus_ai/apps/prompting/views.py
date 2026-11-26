
from apps.auth.permissions import (
    IsAuthenticated,
    IsSuperUser,
)

from fapix.viewsets.websocket import WebSocketApiView

from . import services

from .schemas import (
    ProjectCreateSchema,
    ProjectUpdateSchema,
    PromptSplitSchema,
    PromptSegmentUpdateSchema,
    PromptApprovalSchema,
    AssetRegisterSchema,
    VideoGenerationSubmitSchema,
    JobStatusRequestSchema,
    JobCancelSchema,
    VideoAssemblySchema,
)


# ==========================================================
# PROMPTING ACTION MIXIN
# ==========================================================

class PromptingActionMixin:
    """
    Declarative prompting actions.

    This mixin is inherited by the single central
    RealtimeWebSocketView in apps/realtime/views.py.

    The central WebSocket class must set self.user
    after successful authentication.
    """

    action_schemas = {

        # PROJECTS
        "create_project": ProjectCreateSchema,
        "update_project": ProjectUpdateSchema,

        # PROMPTS
        "split_prompt": PromptSplitSchema,
        "update_prompt_segment": PromptSegmentUpdateSchema,
        "approve_prompt_segments": PromptApprovalSchema,

        # ASSETS
        "register_asset": AssetRegisterSchema,

        # GENERATION
        "submit_video_generation": VideoGenerationSubmitSchema,

        # JOBS
        "get_generation_job": JobStatusRequestSchema,
        "get_job_clips": JobStatusRequestSchema,
        "cancel_generation": JobCancelSchema,

        # ASSEMBLY
        "assemble_video": VideoAssemblySchema,
    }

    action_permissions = {
        "create_project": [IsAuthenticated],
        "list_projects": [IsAuthenticated],
        "get_project": [IsAuthenticated],
        "update_project": [IsAuthenticated],
        "archive_project": [IsAuthenticated],

        "split_prompt": [IsAuthenticated],
        "get_prompt_segments": [IsAuthenticated],
        "update_prompt_segment": [IsAuthenticated],
        "approve_prompt_segments": [IsAuthenticated],

        "register_asset": [IsAuthenticated],
        "list_assets": [IsAuthenticated],
        "delete_asset": [IsAuthenticated],

        "submit_video_generation": [IsAuthenticated],
        "get_generation_job": [IsAuthenticated],
        "get_job_clips": [IsAuthenticated],
        "cancel_generation": [IsAuthenticated],

        "assemble_video": [IsAuthenticated],
    }

    # ======================================================
    # USER HELPER
    # ======================================================

    def _get_user_id(self):

        user = getattr(self, "user", None)

        if user is None:
            raise PermissionError(
                "Authenticated user is unavailable."
            )

        user_id = getattr(user, "id", None)

        if user_id is None:
            raise PermissionError(
                "Invalid authenticated user."
            )

        return user_id

    # ======================================================
    # PROJECT ACTIONS
    # ======================================================

    async def action_create_project(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = ProjectCreateSchema.model_validate(
            payload
        )

        project = await services.create_project(
            self._get_user_id(),
            data,
        )

        return {
            "project": {
                "id": str(project.id),
                "name": project.name,
                "status": project.status,
            }
        }

    async def action_list_projects(
        self,
        payload: dict,
        params: dict = None,
    ):

        projects = await services.get_projects(
            self._get_user_id(),
            limit=payload.get("limit", 50),
            offset=payload.get("offset", 0),
        )

        return {
            "projects": [
                {
                    "id": str(project.id),
                    "name": project.name,
                    "status": project.status,
                    "created_at": project.created_at.isoformat(),
                }
                for project in projects
            ]
        }

    async def action_get_project(
        self,
        payload: dict,
        params: dict = None,
    ):

        project = await services.get_project(
            self._get_user_id(),
            payload["project_id"],
        )

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "total_scenes": project.total_scenes,
            "total_generated_clips": project.total_generated_clips,
            "final_video_url": project.final_video_url,
        }

    async def action_update_project(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = ProjectUpdateSchema.model_validate(
            payload
        )

        project = await services.update_project(
            self._get_user_id(),
            payload["project_id"],
            data,
        )

        return {
            "project_id": str(project.id),
            "name": project.name,
            "status": project.status,
        }

    async def action_archive_project(
        self,
        payload: dict,
        params: dict = None,
    ):

        project = await services.archive_project(
            self._get_user_id(),
            payload["project_id"],
        )

        return {
            "project_id": str(project.id),
            "status": project.status,
        }

    # ======================================================
    # PROMPT ACTIONS
    # ======================================================

    async def action_split_prompt(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = PromptSplitSchema.model_validate(
            payload
        )

        result = await services.split_and_save_prompt(
            user_id=self._get_user_id(),
            prompt=data.prompt,
            project_id=data.project_id,
            separator_mode=data.separator_mode,
        )

        return {
            "project_id": str(result["project"].id),
            "total_segments": len(result["segments"]),
            "segments": [
                {
                    "id": str(segment.id),
                    "sequence": segment.sequence,
                    "prompt": segment.prompt,
                    "title": segment.title,
                    "is_approved": segment.is_approved,
                }
                for segment in result["segments"]
            ],
        }

    async def action_get_prompt_segments(
        self,
        payload: dict,
        params: dict = None,
    ):

        segments = await services.get_prompt_segments(
            self._get_user_id(),
            payload["project_id"],
        )

        return {
            "segments": [
                {
                    "id": str(segment.id),
                    "sequence": segment.sequence,
                    "prompt": segment.prompt,
                    "title": segment.title,
                    "is_approved": segment.is_approved,
                }
                for segment in segments
            ]
        }

    async def action_update_prompt_segment(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = PromptSegmentUpdateSchema.model_validate(
            payload
        )

        segment = await services.update_prompt_segment(
            self._get_user_id(),
            payload["segment_id"],
            data,
        )

        return {
            "segment_id": str(segment.id),
            "sequence": segment.sequence,
            "prompt": segment.prompt,
            "title": segment.title,
        }

    async def action_approve_prompt_segments(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = PromptApprovalSchema.model_validate(
            payload
        )

        segments = await services.approve_prompt_segments(
            self._get_user_id(),
            data.segment_ids,
        )

        return {
            "approved_count": len(segments),
            "segment_ids": [
                str(segment.id)
                for segment in segments
            ],
        }

    # ======================================================
    # ASSET ACTIONS
    # ======================================================

    async def action_register_asset(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = AssetRegisterSchema.model_validate(
            payload
        )

        asset = await services.register_asset(
            self._get_user_id(),
            data,
        )

        return {
            "asset_id": str(asset.id),
            "name": asset.name,
            "storage_provider": asset.storage_provider,
            "storage_key": asset.storage_key,
            "url": asset.url,
        }

    async def action_list_assets(
        self,
        payload: dict,
        params: dict = None,
    ):

        assets = await services.get_project_assets(
            self._get_user_id(),
            payload["project_id"],
        )

        return {
            "assets": [
                {
                    "id": str(asset.id),
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "mime_type": asset.mime_type,
                    "url": asset.url,
                    "file_size": asset.file_size,
                }
                for asset in assets
            ]
        }

    async def action_delete_asset(
        self,
        payload: dict,
        params: dict = None,
    ):

        asset = await services.delete_asset(
            self._get_user_id(),
            payload["asset_id"],
        )

        return {
            "asset_id": str(asset.id),
            "deleted": True,
        }

    # ======================================================
    # GENERATION ACTIONS
    # ======================================================

    async def action_submit_video_generation(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = VideoGenerationSubmitSchema.model_validate(
            payload
        )

        job = await services.submit_generation_job(
            self._get_user_id(),
            data,
        )

        return {
            "job_id": str(job.id),
            "project_id": str(job.project_id),
            "status": job.status,
            "total_clips": job.total_clips,
            "estimated_credits": str(job.estimated_credits),
            "message": "Video generation job submitted.",
        }

    async def action_get_generation_job(
        self,
        payload: dict,
        params: dict = None,
    ):

        job = await services.get_generation_job(
            self._get_user_id(),
            payload["job_id"],
        )

        return {
            "job_id": str(job.id),
            "project_id": str(job.project_id),
            "status": job.status,
            "total_clips": job.total_clips,
            "completed_clips": job.completed_clips,
            "failed_clips": job.failed_clips,
            "estimated_credits": str(job.estimated_credits),
            "actual_credits": str(job.actual_credits),
            "error_message": job.error_message,
        }

    async def action_get_job_clips(
        self,
        payload: dict,
        params: dict = None,
    ):

        clips = await services.get_job_clips(
            self._get_user_id(),
            payload["job_id"],
        )

        return {
            "clips": [
                {
                    "id": str(clip.id),
                    "sequence": clip.sequence,
                    "status": clip.status,
                    "progress": clip.progress,
                    "output_url": clip.output_url,
                    "error_message": clip.error_message,
                }
                for clip in clips
            ]
        }

    async def action_cancel_generation(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = JobCancelSchema.model_validate(
            payload
        )

        job = await services.cancel_generation_job(
            self._get_user_id(),
            data.job_id,
        )

        return {
            "job_id": str(job.id),
            "status": job.status,
        }

    # ======================================================
    # ASSEMBLY ACTION
    # ======================================================

    async def action_assemble_video(
        self,
        payload: dict,
        params: dict = None,
    ):

        data = VideoAssemblySchema.model_validate(
            payload
        )

        if data.clip_ids:
            allowed = await services.get_job_clips(
                self._get_user_id(),
                data.job_id,
            )

            allowed_ids = {
                str(clip.id)
                for clip in allowed
                if clip.status == "completed"
            }

            requested_ids = {
                str(clip_id)
                for clip_id in data.clip_ids
            }

            if not requested_ids.issubset(allowed_ids):
                raise PermissionError(
                    "One or more clips are not available for assembly."
                )

        job = await services.request_video_assembly(
            self._get_user_id(),
            data.job_id,
            project_id=data.project_id,
            clip_ids=data.clip_ids,
        )

        return {
            "job_id": str(job.id),
            "status": job.status,
            "message": "Video assembly queued.",
        }


# ==========================================================
# OPTIONAL ADMIN ACTION MIXIN
# ==========================================================

class PromptingAdminActionMixin:

    action_permissions = {
        "admin_get_generation_job": [IsSuperUser],
    }

    async def action_admin_get_generation_job(
        self,
        payload: dict,
        params: dict = None,
    ):

        job = await services.GenerationJob.get_or_none(
            id=payload["job_id"],
        )

        if not job:
            raise services.JobNotFound(
                "Generation job not found."
            )

        return {
            "job_id": str(job.id),
            "user_id": str(job.user_id),
            "project_id": str(job.project_id),
            "status": job.status,
            "total_clips": job.total_clips,
            "completed_clips": job.completed_clips,
            "failed_clips": job.failed_clips,
        }
