"""
Helpers for monetary values.

Money must be handled with Decimal to avoid binary floating-point rounding
errors in billing, remittance, boleto and reconciliation flows.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


CENT = Decimal("0.01")


def money(value: Any) -> Decimal:
    if value is None:
        value = "0"
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def cents(value: Any) -> int:
    return int((money(value) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def money_float(value: Any) -> float:
    """
    Compatibility bridge for third-party generators that still accept floats.
    Keep Decimal internally and convert only at integration boundaries.
    """
    return float(money(value))
