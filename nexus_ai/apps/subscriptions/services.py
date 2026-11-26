
from decimal import Decimal
from uuid import UUID, uuid4

from datetime import datetime, timezone, timedelta

from tortoise.transactions import in_transaction

from .models import (
    CreditAccount,
    CreditTransaction,
    CreditReservation,
    CreditTransactionType,
    CreditReservationStatus,
)


# ==========================================================
# EXCEPTIONS
# ==========================================================

class InsufficientCredits(Exception):
    pass


class InvalidReservation(Exception):
    pass


class DuplicateTransaction(Exception):
    pass


# ==========================================================
# HELPERS
# ==========================================================

def to_decimal(value) -> Decimal:
    return Decimal(str(value))


async def get_credit_account(user_id: UUID):

    account, _ = await CreditAccount.get_or_create(
        user_id=user_id,
    )

    return account


# ==========================================================
# ADD CREDITS
# ==========================================================

async def add_credits(
    user_id: UUID,
    amount: Decimal,
    transaction_type: str = CreditTransactionType.PURCHASE.value,
    description: str = "",
    reference_id: str | None = None,
    idempotency_key: str | None = None,
    metadata: dict | None = None,
):
    amount = to_decimal(amount)

    if amount <= 0:
        raise ValueError("Credit amount must be positive.")

    async with in_transaction() as conn:

        if idempotency_key:

            existing = await CreditTransaction.filter(
                idempotency_key=idempotency_key
            ).using_db(conn).first()

            if existing:
                if (
                    existing.user_id != user_id
                    or existing.amount != amount
                ):
                    raise DuplicateTransaction(
                        "Idempotency key was already used "
                        "for a different operation."
                    )

                return existing

        await CreditAccount.get_or_create(
            user_id=user_id,
            using_db=conn,
        )

        account = await CreditAccount.filter(
            user_id=user_id
        ).using_db(conn).select_for_update().get()

        before = account.balance

        account.balance += amount
        account.lifetime_earned += amount

        await account.save(
            using_db=conn,
            update_fields=[
                "balance",
                "lifetime_earned",
                "updated_at",
            ],
        )

        transaction = await CreditTransaction.create(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=before,
            balance_after=account.balance,
            description=description,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            metadata=metadata or {},
            using_db=conn,
        )

        return transaction


# ==========================================================
# RESERVE CREDITS
# ==========================================================

async def reserve_credits(
    user_id: UUID,
    amount: Decimal,
    reference_id: str,
    idempotency_key: str,
    expires_minutes: int = 120,
    metadata: dict | None = None,
):
    amount = to_decimal(amount)

    if amount <= 0:
        raise ValueError("Reservation amount must be positive.")

    async with in_transaction() as conn:

        existing = await CreditReservation.filter(
            user_id=user_id,
            idempotency_key=idempotency_key,
        ).using_db(conn).first()

        if existing:

            if (
                existing.amount != amount
                or existing.reference_id != reference_id
            ):
                raise DuplicateTransaction(
                    "Reservation key reused with different parameters."
                )

            return existing

        await CreditAccount.get_or_create(
            user_id=user_id,
            using_db=conn,
        )

        account = await CreditAccount.filter(
            user_id=user_id
        ).using_db(conn).select_for_update().get()

        if account.balance < amount:
            raise InsufficientCredits(
                f"Required: {amount}, Available: {account.balance}"
            )

        before = account.balance

        account.balance -= amount

        await account.save(
            using_db=conn,
            update_fields=["balance", "updated_at"],
        )

        reservation = await CreditReservation.create(
            user_id=user_id,
            amount=amount,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            status=CreditReservationStatus.RESERVED.value,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=expires_minutes),
            metadata=metadata or {},
            using_db=conn,
        )

        await CreditTransaction.create(
            user_id=user_id,
            transaction_type=CreditTransactionType.RESERVATION.value,
            amount=-amount,
            balance_before=before,
            balance_after=account.balance,
            description="Credits reserved for video generation",
            reference_id=reference_id,
            idempotency_key=f"reserve:{reservation.id}",
            metadata={
                "reservation_id": str(reservation.id),
            },
            using_db=conn,
        )

        return reservation


# ==========================================================
# CONSUME RESERVATION
# ==========================================================

async def consume_reservation(reservation_id: UUID):

    async with in_transaction() as conn:

        reservation = await CreditReservation.filter(
            id=reservation_id
        ).using_db(conn).select_for_update().get_or_none()

        if not reservation:
            raise InvalidReservation("Reservation not found.")

        if reservation.status == CreditReservationStatus.CONSUMED.value:
            return reservation

        if reservation.status != CreditReservationStatus.RESERVED.value:
            raise InvalidReservation(
                "Reservation cannot be consumed."
            )

        reservation.status = CreditReservationStatus.CONSUMED.value

        reservation.consumed_at = datetime.now(timezone.utc)

        await reservation.save(
            using_db=conn,
            update_fields=["status", "consumed_at"],
        )

        account = await CreditAccount.filter(
            user_id=reservation.user_id
        ).using_db(conn).select_for_update().get()

        account.lifetime_spent += reservation.amount

        await account.save(
            using_db=conn,
            update_fields=["lifetime_spent", "updated_at"],
        )

        return reservation


# ==========================================================
# RELEASE / REFUND RESERVATION
# ==========================================================

async def release_reservation(
    reservation_id: UUID,
    reason: str = "Generation failed",
):

    async with in_transaction() as conn:

        reservation = await CreditReservation.filter(
            id=reservation_id
        ).using_db(conn).select_for_update().get_or_none()

        if not reservation:
            raise InvalidReservation("Reservation not found.")

        if reservation.status == CreditReservationStatus.RELEASED.value:
            return reservation

        if reservation.status != CreditReservationStatus.RESERVED.value:
            raise InvalidReservation(
                "Only reserved credits can be released."
            )

        account = await CreditAccount.filter(
            user_id=reservation.user_id
        ).using_db(conn).select_for_update().get()

        before = account.balance

        account.balance += reservation.amount

        await account.save(
            using_db=conn,
            update_fields=["balance", "updated_at"],
        )

        await CreditTransaction.create(
            user_id=reservation.user_id,
            transaction_type=CreditTransactionType.REFUND.value,
            amount=reservation.amount,
            balance_before=before,
            balance_after=account.balance,
            description=reason,
            reference_id=reservation.reference_id,
            idempotency_key=f"release:{reservation.id}",
            metadata={
                "reservation_id": str(reservation.id),
            },
            using_db=conn,
        )

        reservation.status = CreditReservationStatus.RELEASED.value

        reservation.released_at = datetime.now(timezone.utc)

        await reservation.save(
            using_db=conn,
            update_fields=["status", "released_at"],
        )

        return reservation


# ==========================================================
# GET USER CREDIT SUMMARY
# ==========================================================

async def get_credit_summary(user_id: UUID):

    account = await get_credit_account(user_id)

    return {
        "balance": account.balance,
        "lifetime_earned": account.lifetime_earned,
        "lifetime_spent": account.lifetime_spent,
    }


# ==========================================================
# GET TRANSACTION HISTORY
# ==========================================================

async def get_credit_history(
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
):

    return await CreditTransaction.filter(
        user_id=user_id
    ).order_by(
        "-created_at"
    ).offset(offset).limit(
        min(limit, 100)
    )


# ==========================================================
# EXPIRE SUBSCRIPTIONS
# ==========================================================

async def expire_subscriptions():

    from .models import UserSubscription

    now = datetime.now(timezone.utc)

    expired = await UserSubscription.filter(
        current_period_end__lte=now,
        status="active",
        cancel_at_period_end=True,
    ).update(
        status="expired",
    )

    return expired


# ==========================================================
# EXPIRE ABANDONED RESERVATIONS
# ==========================================================

async def expire_reservations():

    now = datetime.now(timezone.utc)

    reservations = await CreditReservation.filter(
        status=CreditReservationStatus.RESERVED.value,
        expires_at__lte=now,
    ).limit(200)

    expired_count = 0

    for reservation in reservations:

        try:
            await release_reservation(
                reservation.id,
                reason="Expired generation reservation",
            )

            reservation.status = CreditReservationStatus.EXPIRED.value

            await reservation.save(
                update_fields=["status"],
            )

            expired_count += 1

        except InvalidReservation:
            continue

    return expired_count

from .models import (
    SubscriptionPlan,
    UserSubscription,
    Payment,
    PaymentType,
    PaymentStatus,
    BillingInterval,
    SubscriptionStatus,
)


# ==========================================================
# GET AVAILABLE PLANS
# ==========================================================

async def get_available_plans():

    return await SubscriptionPlan.filter(
        is_active=True,
        is_public=True,
    ).order_by("price")


# ==========================================================
# GET CURRENT SUBSCRIPTION
# ==========================================================

async def get_current_subscription(user_id: UUID):

    return await UserSubscription.filter(
        user_id=user_id,
        status__in=[
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
        ],
    ).select_related(
        "plan"
    ).order_by(
        "-created_at"
    ).first()


# ==========================================================
# CREATE CREDIT PURCHASE PAYMENT
# ==========================================================

async def create_credit_purchase_payment(
    user_id: UUID,
    plan_id: UUID,
    provider: str,
    idempotency_key: str,
):

    existing = await Payment.filter(
        idempotency_key=idempotency_key,
    ).first()

    if existing:

        if existing.user_id != user_id:
            raise DuplicateTransaction(
                "Payment idempotency key belongs to another user."
            )

        return existing

    plan = await SubscriptionPlan.get_or_none(
        id=plan_id,
        is_active=True,
        is_public=True,
    )

    if not plan:
        raise ValueError("Invalid or unavailable plan.")

    if plan.billing_interval != BillingInterval.ONE_TIME.value:
        raise ValueError(
            "This plan is not a one-time credit package."
        )

    if plan.credits_per_period <= 0:
        raise ValueError("This package has no credits.")

    payment = await Payment.create(
        user_id=user_id,
        payment_type=PaymentType.CREDIT_PURCHASE.value,
        status=PaymentStatus.PENDING.value,
        amount=plan.price,
        currency=plan.currency,
        credits_purchased=plan.credits_per_period,
        provider=provider,
        idempotency_key=idempotency_key,
        metadata={
            "plan_id": str(plan.id),
            "plan_name": plan.name,
        },
    )

    return payment


# ==========================================================
# CONFIRM CREDIT PURCHASE
# ==========================================================

async def confirm_credit_purchase(
    payment_id: UUID,
    provider_payment_id: str | None,
    confirmed_by: UUID | None = None,
):
    """
    Call ONLY after verifying the payment provider's
    webhook signature and successful payment status.
    """

    async with in_transaction() as conn:

        payment = await Payment.filter(
            id=payment_id,
        ).using_db(conn).select_for_update().get_or_none()

        if not payment:
            raise ValueError("Payment not found.")

        if payment.status == PaymentStatus.COMPLETED.value:
            return payment

        if payment.payment_type != PaymentType.CREDIT_PURCHASE.value:
            raise ValueError("Unsupported payment type.")

        if payment.status not in (
            PaymentStatus.PENDING.value,
            PaymentStatus.PROCESSING.value,
        ):
            raise ValueError("Payment cannot be completed.")

        if not provider_payment_id and not confirmed_by:
            raise ValueError("Provider payment ID is required.")

        credit_key = f"payment:{payment.id}"
        existing_transaction = await CreditTransaction.filter(
            idempotency_key=credit_key,
        ).using_db(conn).first()
        if existing_transaction:
            if (
                existing_transaction.user_id != payment.user_id
                or existing_transaction.amount != payment.credits_purchased
            ):
                raise DuplicateTransaction(
                    "Payment credit transaction does not match the payment."
                )
        else:
            await CreditAccount.get_or_create(
                user_id=payment.user_id,
                using_db=conn,
            )
            account = await CreditAccount.filter(
                user_id=payment.user_id,
            ).using_db(conn).select_for_update().get()
            before = account.balance
            account.balance += payment.credits_purchased
            account.lifetime_earned += payment.credits_purchased
            await account.save(
                using_db=conn,
                update_fields=["balance", "lifetime_earned", "updated_at"],
            )
            await CreditTransaction.create(
                user_id=payment.user_id,
                transaction_type=CreditTransactionType.PURCHASE.value,
                amount=payment.credits_purchased,
                balance_before=before,
                balance_after=account.balance,
                description="Purchased video generation credits",
                reference_id=str(payment.id),
                idempotency_key=credit_key,
                metadata={
                    "payment_id": str(payment.id),
                    "provider": payment.provider,
                    "manual_confirmation": confirmed_by is not None,
                    "confirmed_by": str(confirmed_by) if confirmed_by else None,
                },
                using_db=conn,
            )

        payment.status = PaymentStatus.COMPLETED.value
        payment.provider_payment_id = provider_payment_id
        payment.paid_at = datetime.now(timezone.utc)
        if confirmed_by:
            payment.metadata = {
                **(payment.metadata or {}),
                "manual_confirmation": True,
                "confirmed_by": str(confirmed_by),
            }

        await payment.save(
            using_db=conn,
            update_fields=[
                "status",
                "provider_payment_id",
                "paid_at",
                "metadata",
                "updated_at",
            ],
        )

        return payment


# ==========================================================
# ADMIN CREDIT ADJUSTMENT
# ==========================================================

async def adjust_credits(
    user_id: UUID,
    amount: Decimal,
    description: str,
    idempotency_key: str,
    adjusted_by: UUID | None = None,
):

    amount = to_decimal(amount)

    if amount == 0:
        raise ValueError("Adjustment cannot be zero.")

    async with in_transaction() as conn:

        existing = await CreditTransaction.filter(
            user_id=user_id,
            idempotency_key=idempotency_key,
        ).using_db(conn).first()

        if existing:

            if existing.amount != amount:
                raise DuplicateTransaction(
                    "Idempotency key reused with a different amount."
                )

            return existing

        await CreditAccount.get_or_create(
            user_id=user_id,
            using_db=conn,
        )

        account = await CreditAccount.filter(
            user_id=user_id
        ).using_db(conn).select_for_update().get()

        before = account.balance

        if account.balance + amount < 0:
            raise InsufficientCredits(
                "Adjustment would result in a negative balance."
            )

        account.balance += amount

        if amount > 0:
            account.lifetime_earned += amount

        await account.save(
            using_db=conn,
            update_fields=[
                "balance",
                "lifetime_earned",
                "updated_at",
            ],
        )

        transaction = await CreditTransaction.create(
            user_id=user_id,
            transaction_type=CreditTransactionType.ADJUSTMENT.value,
            amount=amount,
            balance_before=before,
            balance_after=account.balance,
            description=description,
            idempotency_key=idempotency_key,
            metadata={"adjusted_by": str(adjusted_by)} if adjusted_by else {},
            using_db=conn,
        )

        return transaction
