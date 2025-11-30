from dataclasses import dataclass


@dataclass(frozen=True)
class ProblemId:
    """
    Value Object representing the unique identifier for a problem,
    extracted directly from the HTML (e.g., the 'canselect' span).
    """
    value: str

    def __post_init__(self):
        """Validate the value after initialization."""
        if not self.value or not isinstance(self.value, str) or not self.value.strip():
            raise ValueError(f"ProblemId value must be a non-empty string, got: {self.value!r}")

    def __str__(self):
        return self.value
