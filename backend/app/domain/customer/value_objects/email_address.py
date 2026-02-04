from dataclasses import dataclass
import re


@dataclass(frozen=True)
class EmailAddress:
    """メールアドレス値オブジェクト"""

    value: str

    PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("EmailAddress cannot be empty")
        if len(self.value) > 255:
            raise ValueError("EmailAddress must be 255 characters or less")
        if not self.PATTERN.match(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
