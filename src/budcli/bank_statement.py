import logging
from typing import Callable

import pandas as pd

logger = logging.getLogger(__name__)


class BankStatement:
    """Represents a bank statement."""

    def __init__(
        self, csv_file_path: str, amount_col_name: str, payee_col_name: str
    ) -> None:
        self.amount_col_name = amount_col_name
        self.recipient_col_name = payee_col_name

        # Read the statement csv and preprocess it
        logger.info(f"Reading bank statement from {csv_file_path}")
        df = pd.read_csv(csv_file_path, sep=";")
        logger.info("Preprocessing bank statement data")
        self.statement_df = self._preprocess_bank_data_df(df)  # hard coded for danske

        self.expenses = self.statement_df[self.statement_df[amount_col_name] < 0].copy()
        # Convert to positive numbers
        self.expenses[amount_col_name] = self.expenses[amount_col_name].abs()

        self.income = self.statement_df[self.statement_df[amount_col_name] > 0].copy()

        self.expense_per_recipient = (
            self.expenses.groupby(payee_col_name)[amount_col_name]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        self.recipients = set(self.expense_per_recipient[payee_col_name].tolist())

    # NOTE: Currently hard coded for s pankki
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

    def print_summary(self) -> None:
        print(f"Total expenses: {self.expenses[self.amount_col_name].sum()}")
        print(f"Total income: {self.income[self.amount_col_name].sum()}")
        print(f"Total transactions: {len(self.statement_df)}")

    def get_new_payees(self, existing_recipients: list[str]) -> list[str]:
        """Get those recipients of the statement that are not in the provided list."""
        new_recipients = self.recipients - set(existing_recipients)

        return list(new_recipients)

    def categorize_expenses(
        self, recipient_to_category: Callable[[str], str]
    ) -> pd.DataFrame:
        expense_per_recipient = self.expense_per_recipient.copy()

        expense_per_recipient["Category"] = expense_per_recipient[
            self.recipient_col_name
        ].map(recipient_to_category)

        return (
            expense_per_recipient.groupby("Category")[self.amount_col_name]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
