import typer

app = typer.Typer()


@app.command()
def import_csv(file: str):
    """Import a bank statement CSV file."""
    typer.echo(f"Importing {file}...")


@app.command()
def report():
    """Generate a spending report."""
    typer.echo("Generating report...")


def main():
    app()
