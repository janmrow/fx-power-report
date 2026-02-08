import pytest

from fxpower.domain.models import Currency, Pair, parse_currency, targets_for_base


def test_parse_currency_is_case_insensitive() -> None:
    assert parse_currency("pln") == Currency.PLN
    assert parse_currency(" UsD ") == Currency.USD


def test_parse_currency_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        parse_currency("ABC")


def test_pair_rejects_same_currency() -> None:
    with pytest.raises(ValueError):
        Pair(base=Currency.PLN, quote=Currency.PLN)


def test_pair_code() -> None:
    assert Pair(base=Currency.PLN, quote=Currency.USD).code == "PLN/USD"


def test_targets_for_base_excludes_base() -> None:
    base = Currency.EUR
    targets = targets_for_base(base)
    assert base not in targets
    assert set(targets) == {Currency.PLN, Currency.USD, Currency.GBP}
