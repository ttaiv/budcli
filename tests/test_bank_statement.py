import pandas as pd
import pytest

from budcli.bank_statement import BankStatement
from budcli.statement_parsing import StatementParsingConfig, parse_statement_to_df


@pytest.fixture
def statement(sample_statement_path, sample_config) -> BankStatement:
    df = parse_statement_to_df(sample_statement_path, sample_config)
    return BankStatement(statement_df=df, config=sample_config)


def test_splits_expenses_and_income(statement):
    expenses = statement.get_transactions("expense")
    income = statement.get_transactions("income")

    assert len(expenses) == 11
    assert len(income) == 2
    assert all(t.transaction_type == "expense" for t in expenses)
    assert all(t.transaction_type == "income" for t in income)
    assert len(statement.get_transactions("all")) == 13


def test_amounts_are_positive(statement):
    assert all(t.amount > 0 for t in statement.get_transactions("all"))


def test_income_has_payer(statement):
    payers = {t.payer_name for t in statement.get_transactions("income")}

    assert payers == {"Example Employer Oy", "John Doe"}


def test_missing_payer_column_uses_placeholder():
    config = StatementParsingConfig(
        config_name="test",
        amount_col_name="Amount",
        payee_col_name="Payee",
        date_col_name="Date",
    )
    df = pd.DataFrame(
        {
            "Amount": [-5.0],
            "Payee": ["Shop"],
            "Date": [pd.Timestamp(2025, 1, 1)],
        }
    )

    [transaction] = BankStatement(df, config).get_transactions("expense")

    assert transaction.payer_name == "no payer"


def test_get_transactions_rejects_invalid_type(statement):
    with pytest.raises(ValueError):
        statement.get_transactions("refund")  # type: ignore[arg-type]
