from pathlib import Path

import pytest

from budcli.statement_parsing import StatementParsingConfig

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


@pytest.fixture
def sample_statement_path() -> Path:
    return EXAMPLES_DIR / "sample_statement.csv"


@pytest.fixture
def sample_config() -> StatementParsingConfig:
    return StatementParsingConfig(
        config_name="sample",
        amount_col_name="Amount",
        payee_col_name="Payee",
        date_col_name="Date",
        payer_col_name="Payer",
        csv_delimiter=";",
        date_format="%d.%m.%Y",
    )
