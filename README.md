# budcli

[![CI](https://github.com/ttaiv/budcli/actions/workflows/ci.yml/badge.svg)](https://github.com/ttaiv/budcli/actions/workflows/ci.yml)
![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A command-line budget tracker that eats CSV/Excel bank statements, categorizes
your transactions, and tells you where your money went.

## Features

- **Works with any bank**: describe your bank's export format once (column
  names, date format, delimiter) and reuse it as a named configuration.
- **Learns your categories**: when budcli meets a new payee, it asks for a
  category and can remember the answer, so later statements are categorized
  automatically.
- **Clean payee names**: whitespace, letter case and Finnish characters
  (`ä`, `ö`) are normalized, so `K-MARKET  Keskusta` and `k-market keskusta`
  count as the same payee.
- **Clear summaries**: total income and expenses, spending per category and
  per payee, and every transaction grouped by category.

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```sh
uv tool install git+https://github.com/ttaiv/budcli
```

## Usage

```sh
budcli path/to/statement.csv [--config-name NAME] [--verbose]
```

On the first run, budcli asks which columns of the statement hold the amount,
payee, date and (optionally) payer, and saves that as a named configuration.
Then it asks for a category for each payee it doesn't recognize yet.

You can try it on the included synthetic statement:

```sh
budcli examples/sample_statement.csv
```

Use `Amount`, `Payee`, `Date` and `Payer` as the column names and `%d.%m.%Y`
as the date format. After you categorize the payees, the output looks like this:

```text
---------- Bank statement summary ----------
Total expenses: 1130.02€
Total income: 2600.00€
Total transactions: 13
---------- Income ----------
- Example Employer Oy:    2450.00€
- John Doe:     150.00€
---------- Total expenses per category ----------
Housing       :     850.00€
Groceries     :     197.74€
Sports        :      29.00€
Restaurants   :      24.90€
Subscriptions :      21.98€
Transport     :       6.40€
---------- Total expenses per payee ----------
Example Housing Oy  :     850.00€
Prisma Kaleva       :     116.92€
K-Market Keskusta   :      80.82€
...
```

### Where data is stored

Statement configurations (`statement_configs.json`) and remembered payee
categories (`payee_info.json`) live in your platform's user data directory,
for example `~/.local/share/budcli/` on Linux. Your bank statements are only
read and are never copied anywhere.

## Project structure

```text
src/budcli/
├── cli.py                 # Typer CLI: prompts, orchestration and output
├── statement_parsing.py   # Read CSV/XLSX into a normalized DataFrame; parsing configs
├── bank_statement.py      # Transaction model, split into income and expenses
├── payee_registry.py      # Remembered payee categories, persisted as JSON
└── statement_analysis.py  # Aggregations per payee and per category
```

Built with [Typer](https://typer.tiangolo.com/), [pandas](https://pandas.pydata.org/),
[pydantic](https://docs.pydantic.dev/) and [platformdirs](https://github.com/tox-dev/platformdirs).

## Development

```sh
uv sync                    # install dependencies, including dev tools
uv run pytest              # run tests
uv run ruff check          # lint
uv run ruff format         # format
uv run pyright             # type check
```

## License

[MIT](LICENSE)
