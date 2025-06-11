import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RecipientInfo:
    """Represents information about a recipient"""

    name: str
    category: str | None = None
    # Whether to always ask the user for the category when a payment for this
    # recipient is encountered.
    ask_for_category: bool = False


class RecipientRegistry:
    """A registry for recipient information."""

    def __init__(self) -> None:
        # Set path to to file that will be used to load/save the mapping
        self.file_path = Path.home() / ".budcli" / "recipient_info.json"
        logger.info(f"Looking for recipient info file from {self.file_path}")
        self.recipient_to_info: dict[str, RecipientInfo] = self._load_or_initialize(
            self.file_path
        )

    def _load_or_initialize(
        self, recipient_info_file: Path
    ) -> dict[str, RecipientInfo]:
        """
        Get the recipient info data from the specified file.
        If the file does not exist, an empty dictionary is returned.

        Returns
        -------
        dict

        """
        if recipient_info_file.exists():
            logger.info(f"Loading recipient info from {recipient_info_file}")
            with open(recipient_info_file, "r") as f:
                recipient_info_list = json.load(f)
                recipient_to_info = {
                    info["name"]: RecipientInfo(
                        name=info["name"],
                        category=info.get("category", None),
                        ask_for_category=info.get("ask_for_category", False),
                    )
                    for info in recipient_info_list
                }
        else:
            logger.info(
                f"Recipient info file {recipient_info_file} does not exist. Proceeding with empty info."
            )
            recipient_to_info = {}

        return recipient_to_info

    def get_recipients(self) -> list[str]:
        """Returns a list of all recipients in the registry."""
        return list(self.recipient_to_info)

    def get_recipient_category(self, recipient_name: str) -> str
        """
        Get the category for a recipient.
        If the recipient does not exist, None is returned.
        """
        # Think whether to do this or return whole mapping
        info = self.recipient_to_info.get(recipient_name)
        if info:
            return info.category
        else:
            logger.warning(f"Recipient {recipient_name} not found in registry.")
            return None

    def set_recipient_info(self, info: RecipientInfo) -> None:
        """
        Set the information for a recipient.
        If the recipient already exists, it will be updated.
        If it does not exist, it will be added.
        """
        logger.debug(f"Setting info for recipient {info.name}")
        self.recipient_to_info[info.name] = info

    def save_to_file(self):
        logger.info(f"Saving recipient info to {self.file_path}")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        recipient_info_list = [asdict(info) for info in self.recipient_to_info.values()]
        with open(self.file_path, "w") as f:
            json.dump(recipient_info_list, f, indent=4)
