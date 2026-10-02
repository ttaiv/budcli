import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import budcli.cli
from budcli.statement_parsing import StatementParsingRegistry

KNOWN_PAYEES = {
    "Example Housing Oy": "Housing",
    "K-Market Keskusta": "Groceries",
    "Prisma Kaleva": "Groceries",
    "Spotify": "Subscriptions",
    "Hsl Mobiili": "Transport",
    "Example Gym Oy": "Sports",
}


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch, sample_config) -> Path:
    """Point the app at a temporary data dir pre-seeded with config and payees."""
    monkeypatch.setattr(budcli.cli, "user_data_dir", lambda appname: str(tmp_path))
    StatementParsingRegistry(configs={"sample": sample_config}).save_to_file(
        tmp_path / "statement_configs.json"
    )
    payees = [
        {
            "name": name,
            "primary_category": category,
            "other_categories": [],
            "ask_for_category": False,
        }
        for name, category in KNOWN_PAYEES.items()
    ]
    (tmp_path / "payee_info.json").write_text(json.dumps(payees))
    return tmp_path


def test_cli_categorizes_sample_statement(data_dir: Path, sample_statement_path):
    runner = CliRunner()

    # The only unknown payee is "Ravintola Esimerkki": categorize it and remember it.
    result = runner.invoke(
        budcli.cli.app,
        [str(sample_statement_path), "--config-name", "sample"],
        input="Restaurants\ny\n",
    )

    assert result.exit_code == 0, result.output
    assert "Total expenses: 1130.02€" in result.output
    assert "Total income: 2600.00€" in result.output
    assert "Housing" in result.output
    assert "Restaurants" in result.output

    saved = json.loads((data_dir / "payee_info.json").read_text())
    saved_categories = {p["name"]: p["primary_category"] for p in saved}
    assert saved_categories["Ravintola Esimerkki"] == "Restaurants"
