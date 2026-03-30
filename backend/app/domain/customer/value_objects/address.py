from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Address:
    """住所値オブジェクト"""

    postal_code: str
    prefecture: str
    city: str
    street: str

    POSTAL_CODE_PATTERN = re.compile(r"^\d{3}-\d{4}$")

    def __post_init__(self):
        if not self.postal_code or not self.POSTAL_CODE_PATTERN.match(self.postal_code):
            raise ValueError(
                f"Postal code must be in NNN-NNNN format: {self.postal_code}"
            )

        if not self.prefecture or len(self.prefecture.strip()) == 0:
            raise ValueError("Prefecture cannot be empty")
        if not self.city or len(self.city.strip()) == 0:
            raise ValueError("City cannot be empty")
        if not self.street or len(self.street.strip()) == 0:
            raise ValueError("Street cannot be empty")

        if len(self.prefecture) > 10:
            raise ValueError("Prefecture must be 10 characters or less")
        if len(self.city) > 100:
            raise ValueError("City must be 100 characters or less")
        if len(self.street) > 200:
            raise ValueError("Street must be 200 characters or less")
