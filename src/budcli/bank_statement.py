import logging
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from budcli.statement_parsing import StatementParsingConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Transaction:
    """Represent a bank transaction in the statement."""

    payee_name: str
    payer_name: str
    amount: float
    date: pd.Timestamp
    transaction_type: Literal["expense", "income"]


class BankStatement:
    """Represents a bank statement."""

    def __init__(
        self,
        statement_df: pd.DataFrame,
        config: StatementParsingConfig,
    ) -> None:
        self._statement_df = statement_df
        self._config = config
        # Parse transactions into lists of objects.
        self._expenses: list[Transaction] = self._parse_transactions("expense")
        self._income: list[Transaction] = self._parse_transactions("income")

    def get_transactions(
        self, transaction_type: Literal["expense", "income", "all"] = "all"
    ) -> list[Transaction]:
        """Return a list of transactions of the statement."""
        if transaction_type not in ["expense", "income", "all"]:
            raise ValueError(
                "transaction_type must be one of 'expense', 'income', or 'all'."
            )
        if transaction_type == "expense":
            return self._expenses.copy()
        elif transaction_type == "income":
            return self._income.copy()
        else:  # transaction_type == "all"
            return self._expenses.copy() + self._income.copy()

    def print_summary(self) -> None:
        """Print a summary of the bank statement."""
        total_expenses = sum(transaction.amount for transaction in self._expenses)
        total_income = sum(transaction.amount for transaction in self._income)

        print(f"Total expenses: {total_expenses:.2f}€")
        print(f"Total income: {total_income:.2f}€")
        print(f"Total transactions: {len(self._statement_df)}")

    def _parse_transactions(
        self, transaction_type: Literal["expense", "income"]
    ) -> list[Transaction]:
        """Parse transactions of the given type from the pandas dataframe."""
        assert transaction_type in ["expense", "income"]
        transactions = []
        for _, row in self._statement_df.iterrows():
            amount = row[self._config.amount_col_name]
            row_type = "income" if amount >= 0 else "expense"
            if row_type == transaction_type:
                payer_name = (
                    row[self._config.payer_col_name]
                    if self._config.payer_col_name is not None
                    else "no payer"
                )
                transactions.append(
                    Transaction(
                        payee_name=row[self._config.payee_col_name],
                        payer_name=payer_name,
                        amount=abs(amount),  # amount is always positive
                        date=row[self._config.date_col_name],
                        transaction_type=row_type,
                    )
                )
        return transactions
