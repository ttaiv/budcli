import warnings
from pathlib import Path

from pydantic import BaseModel, Field


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
