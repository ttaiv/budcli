from typing import cast

import pandas as pd
import pytest

from budcli.bank_statement import Transaction
from budcli.statement_analysis import (
    get_total_amount_per_category,
    get_total_expenses_per_payee,
    group_transactions_by_category,
)


def _expense(payee: str, amount: float, day: int = 1) -> Transaction:
    return Transaction(
        payee_name=payee,
        payer_name="me",
        amount=amount,
        # The pandas stubs allow NaT here, but these literal dates are always valid.
        date=cast(pd.Timestamp, pd.Timestamp(year=2025, month=1, day=day)),
        transaction_type="expense",
    )


def test_total_expenses_per_payee():
    expenses = [
        _expense("Shop", 10.0, 1),
        _expense("Shop", 5.5, 2),
        _expense("Gym", 30.0),
    ]

    totals = get_total_expenses_per_payee(expenses)

    assert totals == {"Shop": pytest.approx(15.5), "Gym": pytest.approx(30.0)}


def test_group_and_total_by_category():
    shop1, shop2, gym = (
        _expense("Shop", 10.0, 1),
        _expense("Shop", 5.0, 2),
        _expense("Gym", 30.0),
    )
    expense_to_category = {shop1: "Groceries", shop2: "Groceries", gym: "Sports"}

    grouped = group_transactions_by_category(expense_to_category)
    totals = get_total_amount_per_category(grouped)

    assert grouped == {"Groceries": [shop1, shop2], "Sports": [gym]}
    assert totals == {"Groceries": pytest.approx(15.0), "Sports": pytest.approx(30.0)}
