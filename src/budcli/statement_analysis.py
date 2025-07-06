from collections import defaultdict

from .bank_statement import Transaction


def get_total_expenses_per_payee(expenses: list[Transaction]) -> dict[str, float]:
    """Calculate total expenses per payee."""
    payee_to_total = defaultdict(float)
    for expense in expenses:
        payee_to_total[expense.payee_name] += expense.amount

    return dict(payee_to_total)


def group_transactions_by_category(
    transaction_to_category: dict[Transaction, str],
) -> dict[str, list[Transaction]]:
    """Group transactions by their categories."""
    category_to_transactions: dict[str, list[Transaction]] = defaultdict(list)
    for transaction, category in transaction_to_category.items():
        category_to_transactions[category].append(transaction)

    return dict(category_to_transactions)


def get_total_amount_per_category(
    category_to_transactions: dict[str, list[Transaction]],
) -> dict[str, float]:
    """Calculate the total amount for each category."""
    category_to_total = {
        category: sum(t.amount for t in transactions)
        for category, transactions in category_to_transactions.items()
    }

    return category_to_total
