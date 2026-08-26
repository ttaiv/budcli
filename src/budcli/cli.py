import logging
from pathlib import Path

import typer
from platformdirs import user_config_dir, user_data_dir

import budcli.statement_analysis as analysis
from budcli.bank_statement import (
    BankStatement,
    Transaction,
)
from budcli.payee_registry import Payee, PayeeRegistry
from budcli.statement_parsing import StatementParsingConfig, StatementParsingRegistry

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
def add_statement(
    file_path: str,
    statement_config_name: str = typer.Option(
        None, "--config-name", "-c", help="Name of the statement configuration to use."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output."
    ),
) -> None:
    """Categorize expenses from a bank statement CSV file."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s - %(message)s",
    )
    data_dir = Path(user_data_dir(appname="budcli"))
    data_dir.mkdir(parents=True, exist_ok=True)
    config_dir = Path(user_config_dir(appname="budcli"))
    config_dir.mkdir(parents=True, exist_ok=True)
    parsing_registry_file = config_dir / "statement_configs.json"

    if parsing_registry_file.exists():
        parsing_registry = StatementParsingRegistry.from_file(parsing_registry_file)
    else:
        parsing_registry = StatementParsingRegistry()

    if len(parsing_registry.configs) == 0:
        typer.echo(
            "No statement configurations found in the registry. "
            "Prompting to create a new configuration."
        )
        new_config = _prompt_for_statement_config()
        parsing_registry.configs[new_config.config_name] = new_config
        statement_config_name = new_config.config_name

    if statement_config_name is None:
        typer.echo(
            "Available statement configurations:\n"
            + "\n".join(parsing_registry.configs.keys())
        )
        statement_config_name = typer.prompt(
            "Enter the name of the statement configuration to use"
        )
    if not statement_config_name in parsing_registry.configs:
        typer.echo(
            f"Statement configuration '{statement_config_name}' not found in the registry. "
            "Prompting to create a new configuration."
        )
        new_config = _prompt_for_statement_config()
        parsing_registry.configs[new_config.config_name] = new_config
        statement_config_name = new_config.config_name

    statement_config = parsing_registry.configs[statement_config_name]
    # Save registry to file in case it was updated.
    parsing_registry.save_to_file(parsing_registry_file)

    statement = BankStatement(file_path, config=statement_config)
    # Loads from file or creates a new one.
    payee_registry = PayeeRegistry(info_file_path=data_dir / "payee_info.json")

    statement_expenses = statement.get_transactions("expense")
    statement_income = statement.get_transactions("income")
    if not statement_expenses and not statement_income:
        typer.echo("No expenses or income found in the bank statement.")
        return

    # Calculate total expenses per payee.
    payee_to_total = analysis.get_total_expenses_per_payee(statement_expenses)

    # Categorize each expense and update the payee registry if user chooses to save the category.
    expense_to_category: dict[Transaction, str] = {}
    for expense in statement_expenses:
        if payee_registry.has_payee(expense.payee_name):
            payee_info = payee_registry.get_payee_by_name(expense.payee_name)
            expense_to_category[expense] = payee_info.primary_category
        else:
            category = _prompt_for_category(expense)
            expense_to_category[expense] = category
            # Determine whether to remember this category for this payee in the future.
            remember = typer.confirm(
                "Do you want to automatically categorize payments "
                f"for {expense.payee_name} to category {category} in the future?"
            )
            if remember:
                new_payee_info = Payee(expense.payee_name, primary_category=category)
                payee_registry.add_payee(new_payee_info)

    # Save updated registry
    payee_registry.save_to_file()

    # Group the expenses by category
    category_to_expenses = analysis.group_transactions_by_category(expense_to_category)
    category_to_total = analysis.get_total_amount_per_category(category_to_expenses)
    # Sort categories by total expense descending
    category_to_total_descending = sorted(
        category_to_total.items(), key=lambda x: x[1], reverse=True
    )

    # Print results.
    print("---------- Bank statement summary ----------")
    statement.print_summary()

    if statement_income:
        print("---------- Income ----------")
        for income in statement_income:
            print(f"- {income.payer_name}: {income.amount:10.2f}€")

    if statement_expenses:
        print("---------- Total expenses per category ----------")
        max_category_len = max(
            (len(str(cat)) for cat, _ in category_to_total_descending)
        )
        for category, total in category_to_total_descending:
            print(f"{category:<{max_category_len}} : {total:10.2f}€")

        print("---------- Total expenses per payee ----------")
        max_payee_len = max((len(str(payee)) for payee, _ in payee_to_total.items()))
        for payee, total in sorted(
            payee_to_total.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"{payee:<{max_payee_len}} : {total:10.2f}€")

        print("---------- Transactions in each category ----------")
        for category, total in category_to_total_descending:
            expenses = category_to_expenses[category]
            print(f"{category}: {total:.2f}€ total")
            for expense in expenses:
                print(f"    - {expense.payee_name}: {expense.amount}€")


def main() -> None:
    app()


def _prompt_for_category(expense: Transaction) -> str:
    date_str = expense.date.strftime("%d.%m.%Y")
    category = typer.prompt(
        f"What is the category for payment of {expense.amount}€ "
        f"to {expense.payee_name} on {date_str}"
    )
    return category


def _prompt_and_add_new_payees(
    new_payee_names: list[str], payee_registry: PayeeRegistry
) -> None:
    """Prompt the user for categories of new payees and add them to the registry."""
    for payee_name in new_payee_names:
        category = typer.prompt(f"What is the category for new payee {payee_name}?")
        ask_in_future = typer.confirm(
            f"Do you want to manually categorize '{payee_name}' in the future?",
            default=False,
        )
        payee = Payee(
            payee_name, primary_category=category, ask_for_category=ask_in_future
        )
        payee_registry.add_payee(payee)


def _confirm_and_update_payee_categories(
    payees_to_confirm: list[Payee], payee_registry: PayeeRegistry
) -> None:
    """
    Confirm the categories of a payees and update the registry."""
    for payee in payees_to_confirm:
        category_correct = typer.confirm(
            f"Is the category '{payee.primary_category}' for payee '{payee.name}' correct?",
            default=True,
        )
        if category_correct:
            # No need to update the registry.
            continue
        # Allow user to choose a category from existing ones or add a new one.
        if payee.other_categories:
            typer.echo(f"Choose a category for payee {payee.name}")
            new_category = _prompt_category_multiple_choice(
                options=payee.other_categories
            )
        else:
            new_category = typer.prompt(
                f"Enter the new category for payee {payee.name}"
            )
        payee_registry.update_payee(
            Payee(
                payee.name,
                primary_category=new_category,
                other_categories=list(set(payee.other_categories) | {new_category}),
                ask_for_category=payee.ask_for_category,
            )
        )


def _prompt_category_multiple_choice(options: list[str]) -> str:
    """Prompt the user to choose a category from a list of options or add a new one."""
    option_count = len(options) + 1  # +1 for the option to add a new category
    for i, choice in enumerate(options, start=1):
        typer.echo(f"{i}) {choice}")
    typer.echo(f"{option_count}) Add a new category")

    user_choice = typer.prompt(f"Enter the number of your choice (1-{option_count})")
    if user_choice.isdigit() and 1 <= int(user_choice) <= option_count:
        if int(user_choice) == option_count:
            new_category = typer.prompt("Enter the new category name")
            return new_category
        else:
            return options[int(user_choice) - 1]
    else:
        typer.echo("Invalid choice, please try again.")
        return _prompt_category_multiple_choice(options)


def _prompt_for_statement_config() -> StatementParsingConfig:
    """Prompt the user for the column names of the bank statement."""
    while True:
        config_name = typer.prompt("Enter a name for this statement configuration")
        amount_col_name = typer.prompt("Enter the column name for the amount")
        payee_col_name = typer.prompt("Enter the column name for the payee")
        date_col_name = typer.prompt("Enter the column name for the date")
        payer_col_name = typer.prompt(
            "Enter the column name for the payer (press Enter to skip)",
            default="",
            show_default=False,
        )
        delimiter = typer.prompt(
            "Enter the delimiter used in the CSV file", default=";"
        )
        if len(payer_col_name.strip()) == 0:
            payer_col_name = None

        typer.echo("\n--- Configuration Summary ---")
        typer.echo(f"Config name: {config_name}")
        typer.echo(f"Amount col:  {amount_col_name}")
        typer.echo(f"Date col:    {date_col_name}")
        typer.echo(f"Payee col:   {payee_col_name}")
        typer.echo(f"Payer col:   {payer_col_name}")
        typer.echo(f"Delimiter:   {delimiter}")
        typer.echo("-----------------------------\n")

        if typer.confirm("Is this configuration correct?"):
            return StatementParsingConfig(
                config_name=config_name,
                amount_col_name=amount_col_name,
                date_col_name=date_col_name,
                payee_col_name=payee_col_name,
                payer_col_name=payer_col_name,
                delimiter=delimiter,
            )
        typer.echo("Let's try again...\n")
