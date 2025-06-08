import logging

import typer

from budcli.bank_statement import BankStatement
from budcli.recipient_categories import RecipientCategoryMapping

app = typer.Typer()

logger = logging.getLogger(__name__)


@app.command()
def add_statement(
    file_path: str,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
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
        level=logging.DEBUG,  # if verbose else logging.INFO,
        format="%(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Brrr...")

    statement = BankStatement(
        file_path, amount_col_name="Summa", recipient_col_name="Saajan nimi"
    )
    statement.print_summary()

    recipient_to_category = RecipientCategoryMapping()
    new_recipients = statement.get_new_recipients(
        existing_recipients=recipient_to_category.get_recipients()
    )
    if new_recipients:
        logger.info("New recipients found, prompting for categories...")

        for recipient in new_recipients:
            category = typer.prompt(f"What is the category for recipient {recipient}?")
            recipient_to_category.set_recipient_category(recipient, category)

        recipient_to_category.save_to_file()


@app.command()
def report():
    """Generate a spending report."""
    typer.echo("Generating report...")


def main():
    app()
