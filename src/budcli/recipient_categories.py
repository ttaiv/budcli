import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RecipientCategoryMapping:
    """Represents mapping from a recipient to a category"""

    def __init__(self) -> None:
        # Set path to to file that will be used to load/save the mapping
        self.file_path = Path.home() / ".budcli" / "recipient_categories.json"
        logger.info(
            f"Looking for recipient-category mapping file from {self.file_path}"
        )
        self.recipient_to_category: dict[str, str] = self._load_or_initialize(
            self.file_path
        )

    def _load_or_initialize(self, recipient_category_file: Path) -> dict[str, str]:
        """
        Get the recipient-category mapping from the specified file.
        If the mapping file does not exist, an empty dictionary is returned.

        Returns
        -------
        dict
            Dictionary mapping recipients to categories.
        """
        if recipient_category_file.exists():
            logger.info(
                f"Loading recipient-category mapping from {recipient_category_file}"
            )
            with open(recipient_category_file, "r") as f:
                recipient_to_category = json.load(f)
        else:
            logger.info(
                f"Recipient-category mapping file {recipient_category_file} does not exist. Initializing empty mapping."
            )
            recipient_to_category = {}

        return recipient_to_category

    def get_recipients(self) -> list[str]:
        return list(self.recipient_to_category)

    def set_recipient_category(self, recipient: str, category: str):
        logger.debug(f"Setting category '{category}' for recipient '{recipient}'")
        self.recipient_to_category[recipient] = category

    def save_to_file(self):
        logger.info(f"Saving recipient-category mapping to {self.file_path}")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w") as f:
            json.dump(self.recipient_to_category, f, indent=4)
