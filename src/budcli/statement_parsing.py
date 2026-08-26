import logging
import warnings
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StatementParsingConfig(BaseModel):
    """Configuration for parsing transactions from a bank statement."""

    config_name: str
    amount_col_name: str
    payee_col_name: str
    date_col_name: str
    payer_col_name: str | None = None
    delimiter: str = ";"


class StatementParsingRegistry(BaseModel):
    """Registry for storing statement parsing configurations for different banks."""

    configs: dict[str, StatementParsingConfig] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, file_path: Path) -> "StatementParsingRegistry":
        """Load the registry from a JSON file."""
        if not file_path.exists():
            warnings.warn(
                f"Statement parsing registry file not found at {file_path}. "
                "Creating a new empty registry.",
                category=RuntimeWarning,
            )
            return cls()
        file_text = file_path.read_text()
        return cls.model_validate_json(file_text)

    def save_to_file(self, file_path: Path) -> None:
        """Save the registry to a JSON file."""
        file_path.write_text(self.model_dump_json(indent=2))


def parse_statement_to_df(
    csv_file_path: Path, config: StatementParsingConfig
) -> pd.DataFrame:
    """Parse a bank statement CSV file into a pandas DataFrame."""
    logger.info(f"Reading bank statement from {csv_file_path}")
    df = pd.read_csv(csv_file_path, sep=config.delimiter)
    logger.info("Preprocessing bank statement data")
    return _preprocess_bank_data_df(df, config)


def _preprocess_bank_data_df(
    bank_data_df: pd.DataFrame, config: StatementParsingConfig
) -> pd.DataFrame:
    """Preprocess the bank data dataframe."""
    bank_data_df[config.date_col_name] = pd.to_datetime(
        bank_data_df[config.date_col_name], format="%d.%m.%Y"
    )
    bank_data_df[config.amount_col_name] = pd.to_numeric(
        bank_data_df[config.amount_col_name].str.replace(",", ".")
    )
    bank_data_df[config.payee_col_name] = (
        bank_data_df[config.payee_col_name]
        .str.strip()  # Remove leading/trailing whitespace
        .str.replace("  ", " ")  # Replace double spaces with single space
        .str.lower()
        .str.replace("ä", "a")
        .str.replace("ö", "o")
        .str.title()  # Capitalize the first letter of each word
    )
    bank_data_df[config.payer_col_name] = (
        bank_data_df[config.payer_col_name]
        .str.strip()  # Remove leading/trailing whitespace
        .str.replace("  ", " ")  # Replace double spaces with single space
        .str.lower()
        .str.replace("ä", "a")
        .str.replace("ö", "o")
        .str.title()  # Capitalize the first letter of each word
    )
    # Only keep the relevant columns.
    cols_to_keep = [
        col_name
        for col_name in [
            config.payee_col_name,
            config.payer_col_name,
            config.amount_col_name,
            config.date_col_name,
        ]
        if col_name is not None
    ]
    bank_data_df = bank_data_df[cols_to_keep]

    return bank_data_df
