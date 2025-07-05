import logging
from dataclasses import dataclass
from typing import Callable, Literal

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """Represent a bank transaction in the statement."""

    payee: str
    amount: str
    date: pd.Timestamp
    transaction_type: Literal["expense", "income"]


class BankStatement:
    """Represents a bank statement."""

    def __init__(
        self, csv_file_path: str, amount_col_name: str, payee_col_name: str
    ) -> None:
        self._amount_col_name = amount_col_name
        self._payee_col_name = payee_col_name

        # Read the statement csv and preprocess it
        logger.info(f"Reading bank statement from {csv_file_path}")
        df = pd.read_csv(csv_file_path, sep=";")
        logger.info("Preprocessing bank statement data")
        self._statement_df = self._preprocess_bank_data_df(df)  # hard coded for s-bank

        self._expenses_df = self._statement_df[
            self._statement_df[amount_col_name] < 0
        ].copy()
        # Convert to positive numbers
        self._expenses_df[amount_col_name] = self._expenses_df[amount_col_name].abs()

        self._income_df = self._statement_df[
            self._statement_df[amount_col_name] > 0
        ].copy()

        self._expense_per_payee = (
            self._expenses_df.groupby(payee_col_name)[amount_col_name]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        self._payees = set(self._expense_per_payee[payee_col_name].tolist())

    def get_transactions(
        self, transaction_type: Literal["expense", "income", "all"] = "all"
    ) -> list[Transaction]:
        """Return a list of transactions of the statement."""
        assert transaction_type in ["expense", "income", "all"]
        transactions = []
        for _, row in self._statement_df.iterrows():
            amount = row[self._amount_col_name]
            row_type = "income" if amount >= 0 else "expense"
            if transaction_type == "all" or row_type == transaction_type:
                transactions.append(
                    Transaction(
                        payee=row[self._payee_col_name],
                        amount=abs(amount),  # amount is always positive
                        date=row["Kirjauspäivä"],
                        transaction_type=row_type,
                    )
                )
        return transactions

    def print_summary(self) -> None:
        print(f"Total expenses: {self._expenses_df[self._amount_col_name].sum()}")
        print(f"Total income: {self._income_df[self._amount_col_name].sum()}")
        print(f"Total transactions: {len(self._statement_df)}")

    def get_payees(self) -> set[str]:
        """Get set of payees from the bank statement."""
        return self._payees.copy()

    def categorize_expenses(
        self, recipient_to_category: Callable[[str], str]
    ) -> pd.DataFrame:
        expense_per_recipient = self._expense_per_payee.copy()

        expense_per_recipient["Category"] = expense_per_recipient[
            self._payee_col_name
        ].map(recipient_to_category)

        return (
            expense_per_recipient.groupby("Category")[self._amount_col_name]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

    # NOTE: Currently hard coded for s-bank
    def _preprocess_bank_data_df(self, bank_data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the bank data by converting date columns to datetime format,
        converting the 'Summa' column to numeric, and dropping unnecessary columns.

        Parameters
        ----------
        bank_data : pd.DataFrame
            The bank data to preprocess.

        Returns
        -------
        pd.DataFrame
            The preprocessed bank data.
        """
        bank_data["Kirjauspäivä"] = pd.to_datetime(
            bank_data["Kirjauspäivä"], format="%d.%m.%Y"
        )
        bank_data["Maksupäivä"] = pd.to_datetime(
            bank_data["Maksupäivä"], format="%d.%m.%Y"
        )
        bank_data["Summa"] = pd.to_numeric(bank_data["Summa"].str.replace(",", "."))
        bank_data = bank_data.drop(
            columns=[
                "Saajan tilinumero",
                "Saajan BIC-tunnus",
                "Arkistointitunnus",
                "Viitenumero",
            ]
        )

        return bank_data
