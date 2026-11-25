
import asyncio

from celery import shared_task

from tortoise import Tortoise


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

async def _run_async(coro):

    # Adjust this import to the exact configuration
    # variable exposed by your root db_config.py.
    from db_config import TORTOISE_ORM

    await Tortoise.init(
        config=TORTOISE_ORM,
    )

    try:
        return await coro

    finally:
        await Tortoise.close_connections()


# ==========================================================
# EXPIRE RESERVATIONS
# ==========================================================

@shared_task(
    name="subscriptions.expire_reservations",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def expire_reservations_task(self):

    try:
        from .services import expire_reservations

        return asyncio.run(
            _run_async(expire_reservations())
        )

    except Exception as exc:

        raise self.retry(exc=exc)


# ==========================================================
# EXPIRE SUBSCRIPTIONS
# ==========================================================

@shared_task(
    name="subscriptions.expire_subscriptions",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def expire_subscriptions_task(self):

    try:
        from .services import expire_subscriptions

        return asyncio.run(
            _run_async(expire_subscriptions())
        )

    except Exception as exc:

        raise self.retry(exc=exc)


# ==========================================================
# PAYMENT RECONCILIATION
# ==========================================================

@shared_task(
    name="subscriptions.payment_reconciliation",
)
def payment_reconciliation_task():

    # Provider-specific reconciliation will be implemented
    # when we integrate Stripe or another payment provider.

    return {
        "status": "pending_implementation",
        "message": "Payment provider integration is required.",
    }
