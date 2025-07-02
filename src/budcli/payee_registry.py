import json
import logging
from abc import ABC
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Payee(ABC):
    """Represent a payee in the bank statement."""

    name: str
    primary_category: str
    other_categories: list[str] = field(default_factory=list)
    # Whether the category of this payee should be confirmed by asking the user
    ask_for_category: bool = False


class PayeeRegistry(ABC):
    """Manages information about payees."""

    def __init__(self) -> None:
        # Set path to to file that will be used to load/save payee information.
        self.info_file_path = Path.home() / ".budcli" / "payee_info.json"
        logger.info(f"Looking for payee info file from {self.info_file_path}")
        if self.info_file_path.exists():
            logger.info(f"Payee info file found at {self.info_file_path}")
            self._payee_name_to_payee: dict[str, Payee] = self._load_from_file(
                self.info_file_path
            )
        else:
            logger.info("Payee info file not found, creating a new registry.")
            self._payee_name_to_payee: dict[str, Payee] = {}

    def get_payee_names(self) -> list[str]:
        """Return a list of payee names in the registry."""
        return list(self._payee_name_to_payee)

    def get_payees_to_ask(self) -> list[Payee]:
        """Return a list of payees that require category confirmation."""
        return [
            payee
            for payee in self._payee_name_to_payee.values()
            if payee.ask_for_category
        ]

    '''

    def get_payee_category(self, name: str) -> str:
        """Get the category of a payee by name."""
        payee = self._payee_name_to_payee[name]

        if isinstance(payee, ConstantCategoryPayee):
            return payee.category
        elif isinstance(payee, VariableCategoryPayee):
            return payee.default_category
        else:
            raise TypeError(f"Unknown payee type for {name}.")
    '''

    def add_payee(self, payee: Payee) -> None:
        """Add a new payee to the registry."""
        if payee.name in self._payee_name_to_payee:
            logger.warning(
                f"Payee {payee.name} already exists in the registry, not adding it."
            )
            return
        self._payee_name_to_payee[payee.name] = payee
        logger.debug(
            f"Added payee {payee.name} with primary category {payee.primary_category}."
        )

    def update_payee(self, payee: Payee) -> None:
        """Update an existing payee in the registry."""
        if payee.name not in self._payee_name_to_payee:
            logger.warning(
                f"Payee {payee.name} does not exist in the registry, cannot update it."
            )
            return
        self._payee_name_to_payee[payee.name] = payee
        logger.debug(
            f"Updated payee {payee.name} with primary category {payee.primary_category}."
        )

    def save_to_file(self):
        logger.info(f"Saving payees info to {self.info_file_path}")
        payees_info_list = [
            asdict(payee) for payee in self._payee_name_to_payee.values()
        ]
        self.info_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.info_file_path, "w") as f:
            json.dump(payees_info_list, f, indent=4)

    def _load_from_file(self, payee_info_file: Path) -> dict[str, Payee]:
        """Load the payee info data from the specified file."""
        if not payee_info_file.exists():
            raise FileNotFoundError(
                f"Payee info file {payee_info_file} does not exist."
            )

        logger.info(f"Loading payee info from {payee_info_file}")
        with open(payee_info_file, "r") as f:
            payees_info_list: list[dict] = json.load(f)

        payees = {payee["name"]: Payee(**payee) for payee in payees_info_list}
        logger.info(f"Loaded {len(payees)} payees from file.")
        return payees
