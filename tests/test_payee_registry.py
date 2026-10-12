from pathlib import Path

import pytest

from budcli.payee_registry import Payee, PayeeRegistry


@pytest.fixture
def registry(tmp_path: Path) -> PayeeRegistry:
    return PayeeRegistry(info_file_path=tmp_path / "payee_info.json")


def test_new_registry_is_empty(registry):
    assert registry.get_payee_names() == set()


def test_add_and_get_payee(registry):
    registry.add_payee(Payee("Shop", primary_category="Groceries"))

    assert registry.has_payee("Shop")
    assert registry.get_payee_by_name("Shop").primary_category == "Groceries"


def test_add_existing_payee_does_not_overwrite(registry):
    registry.add_payee(Payee("Shop", primary_category="Groceries"))
    registry.add_payee(Payee("Shop", primary_category="Other"))

    assert registry.get_payee_by_name("Shop").primary_category == "Groceries"


def test_update_payee(registry):
    registry.add_payee(Payee("Shop", primary_category="Groceries"))
    registry.update_payee(Payee("Shop", primary_category="Household"))

    assert registry.get_payee_by_name("Shop").primary_category == "Household"


def test_get_unknown_payee_raises(registry):
    with pytest.raises(KeyError):
        registry.get_payee_by_name("Nobody")


def test_save_and_load_round_trip(tmp_path: Path):
    path = tmp_path / "payee_info.json"
    registry = PayeeRegistry(info_file_path=path)
    payee = Payee(
        "Shop",
        primary_category="Groceries",
        other_categories=["Household"],
        ask_for_category=True,
    )
    registry.add_payee(payee)
    registry.save_to_file()

    loaded = PayeeRegistry(info_file_path=path)

    assert loaded.get_payee_by_name("Shop") == payee
