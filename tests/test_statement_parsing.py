from pathlib import Path

import pandas as pd
import pytest

from budcli.statement_parsing import (
    StatementParsingConfig,
    StatementParsingRegistry,
    parse_statement_to_df,
)


def test_parse_converts_amounts_and_dates(sample_statement_path, sample_config):
    df = parse_statement_to_df(sample_statement_path, sample_config)

    assert pd.api.types.is_numeric_dtype(df["Amount"])
    assert df["Amount"].iloc[0] == pytest.approx(2450.00)
    assert df["Amount"].iloc[2] == pytest.approx(-42.37)
    assert df["Date"].iloc[0] == pd.Timestamp(2025, 3, 1)


def test_parse_normalizes_names(sample_statement_path, sample_config):
    df = parse_statement_to_df(sample_statement_path, sample_config)
    payees = set(df["Payee"])

    # Different spellings of the same payee collapse into one name.
    assert "K-Market Keskusta" in payees
    assert "k-market keskusta" not in payees
    assert "Prisma Kaleva" in payees
    assert "Prisma  Kaleva" not in payees


def test_normalization_replaces_finnish_characters(tmp_path: Path):
    csv_path = tmp_path / "statement.csv"
    csv_path.write_text("Date;Amount;Payee\n01.01.2025;-5,00;  Kärkkäinen Öljy \n")
    config = StatementParsingConfig(
        config_name="test",
        amount_col_name="Amount",
        payee_col_name="Payee",
        date_col_name="Date",
        date_format="%d.%m.%Y",
    )

    df = parse_statement_to_df(csv_path, config)

    assert df["Payee"].iloc[0] == "Karkkainen Oljy"


def test_parse_keeps_only_configured_columns(tmp_path: Path):
    csv_path = tmp_path / "statement.csv"
    csv_path.write_text("Date;Amount;Payee;Reference\n01.01.2025;-5,00;Shop;12345\n")
    config = StatementParsingConfig(
        config_name="test",
        amount_col_name="Amount",
        payee_col_name="Payee",
        date_col_name="Date",
        date_format="%d.%m.%Y",
    )

    df = parse_statement_to_df(csv_path, config)

    assert list(df.columns) == ["Payee", "Amount", "Date"]


def test_parse_rejects_unsupported_format(tmp_path: Path, sample_config):
    path = tmp_path / "statement.txt"
    path.write_text("whatever")

    with pytest.raises(ValueError, match="Unsupported file format"):
        parse_statement_to_df(path, sample_config)


def test_registry_round_trip(tmp_path: Path, sample_config):
    registry_file = tmp_path / "configs.json"
    registry = StatementParsingRegistry(configs={"sample": sample_config})

    registry.save_to_file(registry_file)
    loaded = StatementParsingRegistry.from_file(registry_file)

    assert loaded == registry


def test_registry_from_missing_file_is_empty(tmp_path: Path):
    with pytest.warns(RuntimeWarning):
        registry = StatementParsingRegistry.from_file(tmp_path / "missing.json")

    assert registry.configs == {}
