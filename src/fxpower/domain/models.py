from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Currency(StrEnum):
    PLN = "PLN"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


SUPPORTED_CURRENCIES: tuple[Currency, ...] = (
    Currency.PLN,
    Currency.USD,
    Currency.EUR,
    Currency.GBP,
)


def parse_currency(value: str) -> Currency:
    """Parse user input into a supported Currency (case-insensitive)."""
    normalized = value.strip().upper()
    try:
        return Currency(normalized)
    except ValueError as exc:
        supported = ", ".join([c.value for c in SUPPORTED_CURRENCIES])
        raise ValueError(f"Unsupported currency '{value}'. Supported: {supported}") from exc


@dataclass(frozen=True, slots=True)
class Pair:
    base: Currency
    quote: Currency

    def __post_init__(self) -> None:
        if self.base == self.quote:
            raise ValueError("Pair base and quote must be different.")

    @property
    def code(self) -> str:
        return f"{self.base.value}/{self.quote.value}"


def targets_for_base(base: Currency) -> tuple[Currency, ...]:
    """Return all supported currencies except base, in stable order."""
    return tuple(c for c in SUPPORTED_CURRENCIES if c != base)
