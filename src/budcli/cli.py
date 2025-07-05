import logging
from collections import defaultdict

import typer

from budcli.bank_statement import BankStatement, Transaction
from budcli.payee_registry import Payee, PayeeRegistry

app = typer.Typer()

logger = logging.getLogger(__name__)


@app.command()
def add_statement(file_path: str):
    """
    Import a bank statement CSV file to be processed.

    Parameters
    ----------
    file : str
        The path to the CSV file to import.
    verbose : bool, optional
        If True, enable verbose output. The default is False.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(name)s - %(levelname)s - %(message)s",
    )

    statement = BankStatement(
        file_path, amount_col_name="Summa", payee_col_name="Saajan nimi"
    )
    statement.print_summary()

    payee_registry = PayeeRegistry()  # Loads from file or creates a new one.

    expense_to_category = {}

    for expense in statement.get_transactions("expense"):
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

    # Now group the expenses by category
    category_to_expenses = defaultdict(list[Transaction])
    for expense, category in expense_to_category.items():
        category_to_expenses[category].append(expense)

    category_to_total = _get_total_expenses_per_category(category_to_expenses)

    # Print summary
    print("----------Expense summary by category----------")
    for category, expenses in category_to_expenses.items():
        print(f"{category}: {category_to_total[category]:.2f}€")

    print("----------Transactions in each category---------")
    for category, expenses in category_to_expenses.items():
        print(f"{category}: {category_to_total[category]:.2f}€ total")
        for expense in expenses:
            print(f"    - {expense.payee_name}: {expense.amount}€")


def main():
    app()


def _prompt_for_category(expense: Transaction) -> str:
    date_str = expense.date.strftime("%d.%m.%Y")
    category = typer.prompt(
        f"What is the category for payment of {expense.amount}€ "
        f"to {expense.payee_name} on {date_str}"
    )
    return category


def _get_total_expenses_per_category(
    category_to_expenses: dict[str, list[Transaction]],
) -> dict[str, float]:
    category_to_total = {category: 0.0 for category in category_to_expenses}
    for category, expenses in category_to_expenses.items():
        for expense in expenses:
            category_to_total[category] += expense.amount

    return category_to_total


# Functions below are currently unused.


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
