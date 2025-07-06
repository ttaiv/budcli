import logging
from dataclasses import dataclass
from typing import Literal

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Transaction:
    """Represent a bank transaction in the statement."""

    payee_name: str
    amount: float
    date: pd.Timestamp
    transaction_type: Literal["expense", "income"]


class BankStatement:
    """Represents a bank statement."""

    def __init__(
        self, csv_file_path: str, amount_col_name: str, payee_col_name: str
    ) -> None:
        self._amount_col_name = amount_col_name
        self._payee_col_name = payee_col_name

        # Read the statement to dataframe csv and preprocess it.
        logger.info(f"Reading bank statement from {csv_file_path}")
        df = pd.read_csv(csv_file_path, sep=";")
        logger.info("Preprocessing bank statement data")
        self._statement_df = self._preprocess_bank_data_df(df)  # hard coded for s-bank

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

    def _parse_transactions(
        self, transaction_type: Literal["expense", "income", "all"] = "all"
    ) -> list[Transaction]:
        """Parse transactions from the pandas dataframe."""
        assert transaction_type in ["expense", "income", "all"]
        transactions = []
        for _, row in self._statement_df.iterrows():
            amount = row[self._amount_col_name]
            row_type = "income" if amount >= 0 else "expense"
            if transaction_type == "all" or row_type == transaction_type:
                transactions.append(
                    Transaction(
                        payee_name=row[self._payee_col_name],
                        amount=abs(amount),  # amount is always positive
                        date=row["Kirjauspäivä"],
                        transaction_type=row_type,
                    )
                )
        return transactions
