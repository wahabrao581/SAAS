import json
import os
from decimal import Decimal, InvalidOperation


class ModelPricingNotConfigured(ValueError):
    pass


def _validated_rate(raw_rate, model_name: str, quality: str) -> Decimal:
    try:
        rate = Decimal(str(raw_rate))
    except (InvalidOperation, ValueError) as exc:
        raise ModelPricingNotConfigured(
            f"The {quality} credit rate for model {model_name!r} is invalid."
        ) from exc

    if not rate.is_finite() or rate < 0:
        raise ModelPricingNotConfigured(
            f"The {quality} credit rate for model {model_name!r} must be finite and non-negative."
        )
    return rate


async def get_model_credit_rate(model_name: str, quality: str = "standard") -> Decimal:
    """Return admin-configured credits per second for a model and quality.

    Configure PROMPTING_MODEL_CREDIT_RATES as a JSON object, for example:
    {"model-name": {"standard": "0.25", "high": "0.4", "ultra": "0.6"}}.
    A scalar value remains supported as the legacy rate for every quality.
    """
    from apps.providers.models import ProviderModel

    configured_models = await ProviderModel.filter(
        name=model_name,
        is_active=True,
    )
    database_pricing = []
    for model in configured_models:
        capabilities = model.capabilities or {}
        if not isinstance(capabilities, dict):
            continue
        credit_rates = capabilities.get("credit_rates", {})
        if isinstance(credit_rates, dict) and credit_rates:
            database_pricing.append(credit_rates)

    if database_pricing:
        if any(quality not in rates for rates in database_pricing):
            raise ModelPricingNotConfigured(
                f"No {quality} credit rate is configured for model {model_name!r}."
            )
        rates = {
            _validated_rate(pricing[quality], model_name, quality)
            for pricing in database_pricing
        }
        if len(rates) != 1:
            raise ModelPricingNotConfigured(
                f"Multiple active provider records define different {quality} rates for {model_name!r}; use a unique model key."
            )
        return rates.pop()

    raw_rates = os.getenv("PROMPTING_MODEL_CREDIT_RATES")
    if not raw_rates:
        raise ModelPricingNotConfigured(
            "PROMPTING_MODEL_CREDIT_RATES is not configured."
        )

    try:
        rates = json.loads(raw_rates)
    except json.JSONDecodeError as exc:
        raise ModelPricingNotConfigured(
            "PROMPTING_MODEL_CREDIT_RATES must contain a JSON object."
        ) from exc

    if not isinstance(rates, dict):
        raise ModelPricingNotConfigured(
            "PROMPTING_MODEL_CREDIT_RATES must contain a JSON object."
        )

    raw_rate = rates.get(model_name)
    if raw_rate is None:
        raise ModelPricingNotConfigured(
            f"No credit rate is configured for model {model_name!r}."
        )
    if isinstance(raw_rate, dict):
        raw_rate = raw_rate.get(quality)
        if raw_rate is None:
            raise ModelPricingNotConfigured(
                f"No {quality} credit rate is configured for model {model_name!r}."
            )
    elif not isinstance(raw_rate, (str, int, float, Decimal)):
        raise ModelPricingNotConfigured(
            f"The {quality} credit rate for model {model_name!r} must be a number."
        )
    return _validated_rate(raw_rate, model_name, quality)
