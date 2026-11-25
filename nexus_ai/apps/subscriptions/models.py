
import uuid

from enum import Enum
from tortoise import fields, models


# ==========================================================
# ENUMS
# ==========================================================

class BillingInterval(str, Enum):
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentType(str, Enum):
    SUBSCRIPTION = "subscription"
    CREDIT_PURCHASE = "credit_purchase"


class CreditTransactionType(str, Enum):
    PURCHASE = "purchase"
    SUBSCRIPTION = "subscription"
    RESERVATION = "reservation"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    BONUS = "bonus"


class CreditReservationStatus(str, Enum):
    RESERVED = "reserved"
    CONSUMED = "consumed"
    RELEASED = "released"
    EXPIRED = "expired"


# ==========================================================
# SUBSCRIPTION PLAN
# ==========================================================

class SubscriptionPlan(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    name = fields.CharField(
        max_length=100,
        unique=True,
    )

    slug = fields.CharField(
        max_length=100,
        unique=True,
    )

    description = fields.TextField(
        null=True,
    )

    price = fields.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    currency = fields.CharField(
        max_length=10,
        default="USD",
    )

    billing_interval = fields.CharField(
        max_length=30,
        default=BillingInterval.MONTHLY.value,
    )

    credits_per_period = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    is_active = fields.BooleanField(
        default=True,
    )

    is_public = fields.BooleanField(
        default=True,
    )

    # Optional plan configuration.
    features = fields.JSONField(
        default=dict,
    )

    # Maximum concurrent generation jobs.
    max_concurrent_jobs = fields.IntField(
        default=1,
    )

    # Optional maximum output resolution.
    max_resolution = fields.CharField(
        max_length=30,
        default="720p",
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "subscription_plans"
        ordering = ["price"]

    def __str__(self):
        return self.name


# ==========================================================
# USER SUBSCRIPTION
# ==========================================================

class UserSubscription(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    user = fields.ForeignKeyField(
        "models.User",
        related_name="subscriptions",
        on_delete=fields.CASCADE,
    )

    plan = fields.ForeignKeyField(
        "models.SubscriptionPlan",
        related_name="user_subscriptions",
        on_delete=fields.RESTRICT,
    )

    status = fields.CharField(
        max_length=30,
        default=SubscriptionStatus.ACTIVE.value,
    )

    started_at = fields.DatetimeField()

    current_period_start = fields.DatetimeField()

    current_period_end = fields.DatetimeField(
        null=True,
    )

    cancel_at_period_end = fields.BooleanField(
        default=False,
    )

    canceled_at = fields.DatetimeField(
        null=True,
    )

    # External payment provider identifiers.
    provider = fields.CharField(
        max_length=50,
        null=True,
    )

    provider_subscription_id = fields.CharField(
        max_length=255,
        null=True,
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
        table = "user_subscriptions"
        ordering = ["-created_at"]
        indexes = [
            ("status", "current_period_end"),
        ]


# ==========================================================
# CREDIT ACCOUNT
# ==========================================================

class CreditAccount(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    user = fields.ForeignKeyField(
        "models.User",
        related_name="credit_accounts",
        on_delete=fields.CASCADE,
        unique=True,
    )

    # Available credits.
    balance = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    # Lifetime statistics.
    lifetime_earned = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    lifetime_spent = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    updated_at = fields.DatetimeField(
        auto_now=True,
    )

    class Meta:
        table = "credit_accounts"


# ==========================================================
# CREDIT TRANSACTION LEDGER
# ==========================================================

class CreditTransaction(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    user = fields.ForeignKeyField(
        "models.User",
        related_name="credit_transactions",
        on_delete=fields.CASCADE,
    )

    transaction_type = fields.CharField(
        max_length=30,
    )

    # Positive = credits added.
    # Negative = credits removed.
    amount = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
    )

    balance_before = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
    )

    balance_after = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
    )

    description = fields.TextField(
        null=True,
    )

    # Related payment, generation job, reservation, etc.
    reference_id = fields.CharField(
        max_length=255,
        null=True,
    )

    idempotency_key = fields.CharField(
        max_length=255,
        null=True,
        unique=True,
    )

    metadata = fields.JSONField(
        default=dict,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    class Meta:
        table = "credit_transactions"
        ordering = ["-created_at"]
        indexes = [
            ("user", "created_at"),
            ("transaction_type", "created_at"),
        ]


# ==========================================================
# CREDIT RESERVATION
# ==========================================================

class CreditReservation(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    user = fields.ForeignKeyField(
        "models.User",
        related_name="credit_reservations",
        on_delete=fields.CASCADE,
    )

    amount = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
    )

    status = fields.CharField(
        max_length=30,
        default=CreditReservationStatus.RESERVED.value,
    )

    # ID of the generation job.
    reference_id = fields.CharField(
        max_length=255,
    )

    idempotency_key = fields.CharField(
        max_length=255,
    )

    expires_at = fields.DatetimeField(
        null=True,
    )

    consumed_at = fields.DatetimeField(
        null=True,
    )

    released_at = fields.DatetimeField(
        null=True,
    )

    metadata = fields.JSONField(
        default=dict,
    )

    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    class Meta:
        table = "credit_reservations"
        unique_together = [
            ("user", "idempotency_key"),
        ]
        indexes = [
            ("status", "expires_at"),
            ("user", "created_at"),
        ]


# ==========================================================
# PAYMENTS
# ==========================================================

class Payment(models.Model):

    id = fields.UUIDField(
        pk=True,
        default=uuid.uuid4,
    )

    user = fields.ForeignKeyField(
        "models.User",
        related_name="payments",
        on_delete=fields.RESTRICT,
    )

    subscription = fields.ForeignKeyField(
        "models.UserSubscription",
        related_name="payments",
        null=True,
        on_delete=fields.SET_NULL,
    )

    payment_type = fields.CharField(
        max_length=30,
    )

    status = fields.CharField(
        max_length=30,
        default=PaymentStatus.PENDING.value,
    )

    amount = fields.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    currency = fields.CharField(
        max_length=10,
        default="USD",
    )

    credits_purchased = fields.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )

    provider = fields.CharField(
        max_length=50,
    )

    provider_payment_id = fields.CharField(
        max_length=255,
        null=True,
    )

    idempotency_key = fields.CharField(
        max_length=255,
        unique=True,
    )

    paid_at = fields.DatetimeField(
        null=True,
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
        table = "payments"
        ordering = ["-created_at"]
        indexes = [
            ("user", "created_at"),
            ("status", "created_at"),
        ]
