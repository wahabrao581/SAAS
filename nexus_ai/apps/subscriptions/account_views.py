import calendar
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import Depends, HTTPException, status
from tortoise.transactions import in_transaction

from apps.auth.models import User
from apps.auth.permissions import IsSuperUser, get_current_active_user, permission_required
from apps.prompting.config import ModelPricingNotConfigured, get_model_credit_rate
from apps.prompting.models import Asset, ClipAsset, PromptSegment, VideoClip, VideoProject
from apps.providers.models import ProviderModel

from .models import (
    CreditAccount,
    CreditTransaction,
    CreditTransactionType,
    Payment,
    PaymentStatus,
    SubscriptionPlan,
    SubscriptionStatus,
    UserSubscription,
)
from .schemas import (
    AdminCreditAdjustment,
    AdminModelAccessUpdate,
    AdminPaymentConfirmation,
    AdminSubscriptionAssignment,
    CreditEstimateRequest,
)
from .services import (
    adjust_credits,
    confirm_credit_purchase,
    get_available_plans,
    get_credit_history,
    get_credit_summary,
    get_current_subscription,
)


admin_required = permission_required(IsSuperUser())


def safe_asset_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme and parsed.scheme.lower() not in ("http", "https"):
        return None
    if not parsed.scheme and (parsed.netloc or value.startswith("//")):
        return None
    return value


async def account_overview(user: User = Depends(get_current_active_user)):
    credits = await get_credit_summary(user.id)
    transactions = await get_credit_history(user.id, limit=10)
    subscription = await get_current_subscription(user.id)
    models = await ProviderModel.filter(is_active=True).order_by("name")
    plans = await get_available_plans()
    visible_models = [
        {
            "name": model.name,
            "display_name": model.display_name,
            "capabilities": {
                key: value
                for key, value in (
                    model.capabilities
                    if isinstance(model.capabilities, dict)
                    else {}
                ).items()
                if key != "credit_rates"
            },
        }
        for model in models
        if user.allowed_models is None or model.name in user.allowed_models
    ]

    return {
        "profile": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "role": user.role,
            "allowed_models": user.allowed_models,
        },
        "credits": credits,
        "transactions": transactions,
        "subscription": (
            {
                "id": subscription.id,
                "status": subscription.status,
                "plan": {
                    "id": subscription.plan.id,
                    "name": subscription.plan.name,
                    "billing_interval": subscription.plan.billing_interval,
                    "credits_per_period": subscription.plan.credits_per_period,
                },
                "current_period_end": subscription.current_period_end,
            }
            if subscription
            else None
        ),
        "models": visible_models,
        "plans": [
            {
                "id": plan.id,
                "name": plan.name,
                "slug": plan.slug,
                "description": plan.description,
                "price": plan.price,
                "currency": plan.currency,
                "billing_interval": plan.billing_interval,
                "credits_per_period": plan.credits_per_period,
                "features": plan.features,
            }
            for plan in plans
        ],
    }


async def available_plans(_: User = Depends(get_current_active_user)):
    plans = await get_available_plans()
    return [
        {
            "id": plan.id,
            "name": plan.name,
            "slug": plan.slug,
            "description": plan.description,
            "price": plan.price,
            "currency": plan.currency,
            "billing_interval": plan.billing_interval,
            "credits_per_period": plan.credits_per_period,
            "features": plan.features,
        }
        for plan in plans
    ]


async def project_history(user: User = Depends(get_current_active_user)):
    projects = await VideoProject.filter(user_id=user.id).order_by("-updated_at")
    segments = (
        await PromptSegment.filter(
            project_id__in=[project.id for project in projects],
        ).order_by("sequence")
        if projects
        else []
    )
    prompts_by_project = defaultdict(list)
    for segment in segments:
        prompts_by_project[segment.project_id].append(
            {
                "id": segment.id,
                "sequence": segment.sequence,
                "title": segment.title,
                "prompt": segment.prompt,
                "is_approved": segment.is_approved,
                "updated_at": segment.updated_at,
            }
        )
    return {
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "original_prompt": project.original_prompt,
                "status": project.status,
                "default_model": project.default_model,
                "total_scenes": project.total_scenes,
                "total_generated_clips": project.total_generated_clips,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "prompts": prompts_by_project[project.id],
            }
            for project in projects
        ],
    }


async def estimate_credits(
    data: CreditEstimateRequest,
    user: User = Depends(get_current_active_user),
):
    if user.allowed_models is not None and data.model_name not in user.allowed_models:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your account does not have access to model {data.model_name!r}.",
        )
    try:
        rate = await get_model_credit_rate(data.model_name, data.quality)
    except ModelPricingNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    per_scene = (rate * data.duration_seconds).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )
    total = (per_scene * data.scene_count).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )
    return {
        "model_name": data.model_name,
        "quality": data.quality,
        "rate_per_second": rate,
        "duration_seconds": data.duration_seconds,
        "scene_count": data.scene_count,
        "per_scene": per_scene,
        "total": total,
        "credit_balance": (await get_credit_summary(user.id))["balance"],
    }


async def admin_user_details(
    user_id: UUID,
    _: User = Depends(admin_required),
):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    credit_summary = await get_credit_summary(user.id)
    transactions = await get_credit_history(user.id, limit=50)
    subscriptions = await UserSubscription.filter(user_id=user.id).select_related(
        "plan"
    ).order_by("-created_at")
    payments = await Payment.filter(user_id=user.id).order_by("-created_at").limit(100)
    projects = await VideoProject.filter(user_id=user.id).order_by("-updated_at")

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "allowed_models": user.allowed_models,
            "created_at": user.created_at,
        },
        "credits": credit_summary,
        "transactions": transactions,
        "subscriptions": [
            {
                "id": subscription.id,
                "status": subscription.status,
                "plan": {
                    "id": subscription.plan.id,
                    "name": subscription.plan.name,
                    "slug": subscription.plan.slug,
                },
                "started_at": subscription.started_at,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "metadata": subscription.metadata,
            }
            for subscription in subscriptions
        ],
        "payments": [
            {
                "id": payment.id,
                "payment_type": payment.payment_type,
                "status": payment.status,
                "amount": payment.amount,
                "currency": payment.currency,
                "credits_purchased": payment.credits_purchased,
                "provider": payment.provider,
                "provider_payment_id": payment.provider_payment_id,
                "paid_at": payment.paid_at,
                "created_at": payment.created_at,
            }
            for payment in payments
        ],
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "total_scenes": project.total_scenes,
                "total_generated_clips": project.total_generated_clips,
                "updated_at": project.updated_at,
            }
            for project in projects
        ],
    }


async def admin_project_details(
    project_id: UUID,
    _: User = Depends(admin_required),
):
    project = await VideoProject.filter(id=project_id).select_related("user").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    prompts = await PromptSegment.filter(project_id=project.id).order_by("sequence")
    assets = await Asset.filter(
        project_id=project.id,
        is_deleted=False,
    ).order_by("-created_at")
    clips = await VideoClip.filter(project_id=project.id).order_by("sequence")
    asset_links = (
        await ClipAsset.filter(
            clip_id__in=[clip.id for clip in clips],
        ).select_related("asset")
        if clips
        else []
    )
    links_by_clip = defaultdict(list)
    for link in asset_links:
        links_by_clip[link.clip_id].append(link)

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "original_prompt": project.original_prompt,
            "status": project.status,
            "default_model": project.default_model,
            "default_settings": project.default_settings,
            "final_video_url": safe_asset_url(project.final_video_url),
            "total_scenes": project.total_scenes,
            "total_generated_clips": project.total_generated_clips,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "user": {
                "id": project.user.id,
                "email": project.user.email,
                "username": project.user.username,
            },
        },
        "prompts": [
            {
                "id": prompt.id,
                "sequence": prompt.sequence,
                "title": prompt.title,
                "prompt": prompt.prompt,
                "is_approved": prompt.is_approved,
                "created_at": prompt.created_at,
            }
            for prompt in prompts
        ],
        "assets": [
            {
                "id": asset.id,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "mime_type": asset.mime_type,
                "file_size": asset.file_size,
                "storage_provider": asset.storage_provider,
                "url": safe_asset_url(asset.url),
                "created_at": asset.created_at,
            }
            for asset in assets
        ],
        "clips": [
            {
                "id": clip.id,
                "sequence": clip.sequence,
                "prompt": clip.prompt,
                "model_name": clip.model_name,
                "status": clip.status,
                "settings": clip.settings,
                "output_url": safe_asset_url(clip.output_url),
                "error_message": clip.error_message,
                "assets": [
                    {
                        "id": link.asset.id,
                        "name": link.asset.name,
                        "role": link.role,
                        "url": safe_asset_url(link.asset.url),
                    }
                    for link in links_by_clip[clip.id]
                ],
            }
            for clip in clips
        ],
    }


async def admin_adjust_user_credits(
    user_id: UUID,
    data: AdminCreditAdjustment,
    actor: User = Depends(admin_required),
):
    if not await User.exists(id=user_id):
        raise HTTPException(status_code=404, detail="User not found.")
    try:
        transaction = await adjust_credits(
            user_id=user_id,
            amount=data.amount,
            description=data.description,
            idempotency_key=data.idempotency_key,
            adjusted_by=actor.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return transaction


async def admin_set_model_access(
    user_id: UUID,
    data: AdminModelAccessUpdate,
    _: User = Depends(admin_required),
):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if data.allowed_models is not None:
        model_names = set(
            await ProviderModel.filter(
                is_active=True,
                name__in=data.allowed_models,
            ).values_list("name", flat=True)
        )
        unknown = sorted(set(data.allowed_models) - model_names)
        if unknown:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown or inactive model keys: {', '.join(unknown)}",
            )
        if len(set(data.allowed_models)) != len(data.allowed_models):
            raise HTTPException(status_code=422, detail="Model keys must be unique.")

    user.allowed_models = data.allowed_models
    await user.save(update_fields=["allowed_models", "updated_at"])
    return {"user_id": user.id, "allowed_models": user.allowed_models}


async def admin_assign_subscription(
    user_id: UUID,
    data: AdminSubscriptionAssignment,
    actor: User = Depends(admin_required),
):
    user = await User.get_or_none(id=user_id)
    plan = await SubscriptionPlan.get_or_none(id=data.plan_id, is_active=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if not plan:
        raise HTTPException(status_code=404, detail="Active subscription plan not found.")

    now = datetime.now(timezone.utc)
    end = data.current_period_end
    if end is not None and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if end is None and plan.billing_interval in ("monthly", "yearly"):
        months = 1 if plan.billing_interval == "monthly" else 12
        month_index = now.month - 1 + months
        year = now.year + month_index // 12
        month = month_index % 12 + 1
        end = now.replace(
            year=year,
            month=month,
            day=min(now.day, calendar.monthrange(year, month)[1]),
        )
    if end is not None and end <= now:
        raise HTTPException(status_code=422, detail="Subscription end must be in the future.")

    async with in_transaction() as conn:
        await UserSubscription.filter(
            user_id=user.id,
            status__in=[SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value],
        ).using_db(conn).update(
            status=SubscriptionStatus.CANCELED.value,
            canceled_at=now,
        )
        subscription = await UserSubscription.create(
            user_id=user.id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE.value,
            started_at=now,
            current_period_start=now,
            current_period_end=end,
            provider="manual-admin",
            metadata={
                "assigned_by": str(actor.id),
                "note": data.note,
            },
            using_db=conn,
        )
        if plan.credits_per_period > 0:
            await CreditAccount.get_or_create(user_id=user.id, using_db=conn)
            account = await CreditAccount.filter(
                user_id=user.id,
            ).using_db(conn).select_for_update().get()
            balance_before = account.balance
            account.balance += plan.credits_per_period
            account.lifetime_earned += plan.credits_per_period
            await account.save(
                using_db=conn,
                update_fields=["balance", "lifetime_earned", "updated_at"],
            )
            await CreditTransaction.create(
                user_id=user.id,
                transaction_type=CreditTransactionType.SUBSCRIPTION.value,
                amount=plan.credits_per_period,
                balance_before=balance_before,
                balance_after=account.balance,
                description=f"Credits granted with {plan.name} subscription",
                reference_id=str(subscription.id),
                idempotency_key=f"admin-subscription:{subscription.id}",
                metadata={
                    "subscription_id": str(subscription.id),
                    "plan_id": str(plan.id),
                    "assigned_by": str(actor.id),
                },
                using_db=conn,
            )
    return {
        "id": subscription.id,
        "user_id": user.id,
        "plan_id": plan.id,
        "status": subscription.status,
        "current_period_end": subscription.current_period_end,
        "credits_granted": plan.credits_per_period,
    }


async def admin_confirm_payment(
    payment_id: UUID,
    data: AdminPaymentConfirmation,
    actor: User = Depends(admin_required),
):
    payment = await Payment.get_or_none(id=payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")
    if payment.status == PaymentStatus.COMPLETED.value:
        return payment
    try:
        return await confirm_credit_purchase(
            payment_id=payment_id,
            provider_payment_id=data.provider_payment_id,
            confirmed_by=actor.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
