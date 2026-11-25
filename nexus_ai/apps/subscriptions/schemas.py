
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# SUBSCRIPTION PLANS
# ==========================================================

class SubscriptionPlanRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None

    price: Decimal
    currency: str
    billing_interval: str

    credits_per_period: Decimal

    is_active: bool
    is_public: bool

    features: dict = Field(default_factory=dict)

    max_concurrent_jobs: int
    max_resolution: str

    created_at: datetime


class SubscriptionPlanCreate(BaseModel):

    name: str = Field(min_length=2, max_length=100)

    slug: str = Field(min_length=2, max_length=100)

    description: str | None = None

    price: Decimal = Field(ge=0)

    currency: str = "USD"

    billing_interval: str = "monthly"

    credits_per_period: Decimal = Field(ge=0)

    is_active: bool = True

    is_public: bool = True

    features: dict = Field(default_factory=dict)

    max_concurrent_jobs: int = Field(default=1, ge=1)

    max_resolution: str = "720p"


class SubscriptionPlanUpdate(BaseModel):

    name: str | None = None

    slug: str | None = None

    description: str | None = None

    price: Decimal | None = Field(default=None, ge=0)

    currency: str | None = None

    billing_interval: str | None = None

    credits_per_period: Decimal | None = Field(default=None, ge=0)

    is_active: bool | None = None

    is_public: bool | None = None

    features: dict | None = None

    max_concurrent_jobs: int | None = Field(default=None, ge=1)

    max_resolution: str | None = None


# ==========================================================
# USER SUBSCRIPTIONS
# ==========================================================

class UserSubscriptionRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    status: str

    plan_id: UUID

    started_at: datetime

    current_period_start: datetime

    current_period_end: datetime | None = None

    cancel_at_period_end: bool

    canceled_at: datetime | None = None

    created_at: datetime


# ==========================================================
# CREDIT ACCOUNT
# ==========================================================

class CreditAccountRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    balance: Decimal

    lifetime_earned: Decimal

    lifetime_spent: Decimal

    updated_at: datetime


# ==========================================================
# CREDIT TRANSACTIONS
# ==========================================================

class CreditTransactionRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    transaction_type: str

    amount: Decimal

    balance_before: Decimal

    balance_after: Decimal

    description: str | None = None

    reference_id: str | None = None

    metadata: dict = Field(default_factory=dict)

    created_at: datetime


# ==========================================================
# CREDIT RESERVATION
# ==========================================================

class CreditReservationRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    amount: Decimal

    status: str

    reference_id: str

    expires_at: datetime | None = None

    consumed_at: datetime | None = None

    released_at: datetime | None = None

    created_at: datetime


# ==========================================================
# PAYMENT
# ==========================================================

class PaymentRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    payment_type: str

    status: str

    amount: Decimal

    currency: str

    credits_purchased: Decimal

    provider: str

    provider_payment_id: str | None = None

    paid_at: datetime | None = None

    created_at: datetime


class PaymentCreate(BaseModel):

    payment_type: str

    provider: str

    # A plan or credit package identifier.
    product_id: UUID

    idempotency_key: str = Field(
        min_length=8,
        max_length=255,
    )


# ==========================================================
# ADMIN CREDIT ADJUSTMENT
# ==========================================================

class CreditAdjustmentSchema(BaseModel):

    user_id: UUID

    amount: Decimal

    description: str = Field(
        min_length=5,
        max_length=500,
    )

    idempotency_key: str = Field(
        min_length=8,
        max_length=255,
    )


# ==========================================================
# ADMIN PAYMENT STATUS
# ==========================================================

class PaymentStatusUpdate(BaseModel):

    status: str


class CreditEstimateRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)
    quality: Literal["standard", "high", "ultra"] = "standard"
    duration_seconds: Decimal = Field(gt=0, le=60)
    scene_count: int = Field(gt=0, le=1000)


class AdminCreditAdjustment(BaseModel):
    amount: Decimal
    description: str = Field(min_length=5, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=255)


class AdminModelAccessUpdate(BaseModel):
    allowed_models: list[str] | None = Field(max_length=100)


class AdminSubscriptionAssignment(BaseModel):
    plan_id: UUID
    current_period_end: datetime | None = None
    note: str = Field(default="Manual admin assignment", min_length=5, max_length=500)


class AdminPaymentConfirmation(BaseModel):
    provider_payment_id: str | None = Field(default=None, max_length=255)
