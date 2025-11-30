from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Problem:
    """
    Domain Entity representing an EGE problem after scraping and processing.

    This entity holds the core data of the problem as scraped from FIPI,
    including computed attributes like difficulty level, task number, etc.
    It does NOT hold user-specific data like solving status or attempts.
    """
    # Identifier for the problem (extracted from HTML task_id)
    problem_id: str

    # Subject information (name only)
    subject_name: str

    # Main problem statement text
    text: str

    # Source URL where the problem was scraped from
    source_url: str

    # Computed/Inferred attributes (optional)
    difficulty_level: Optional[str] = None  # e.g., "basic", "advanced", or None
    task_number: Optional[int] = None      # 1-19 or None
    exam_part: Optional[str] = None        # e.g., "Part 1", "Part 2" or None

    # Extracted attributes
    answer: Optional[str] = None           # Correct answer if known
    images: List[str] = field(default_factory=list)               # List of paths to associated images
    files: List[str] = field(default_factory=list)                # List of paths to associated files
    kes_codes: List[str] = field(default_factory=list)            # KES codes extracted from HTML
    topics: List[str] = field(default_factory=list)               # Topics derived from KES codes
    kos_codes: List[str] = field(default_factory=list)            # KOS codes extracted from HTML
    form_id: Optional[str] = None          # Form ID if present in HTML

    # FIPI project specific attribute
    fipi_proj_id: Optional[str] = None     # ID of the FIPI project this problem belongs to

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate the problem after initialization."""
        # Initialize default values for mutable defaults
        if self.updated_at is None:
            self.updated_at = datetime.now()

        # Validate the problem according to business rules
        self._validate()

    def _validate(self):
        """Internal validation method to avoid circular imports."""
        # Validate text
        if not self.text or not self.text.strip():
            raise ValueError("Problem text cannot be empty")

        # Validate exam_part if present
        if self.exam_part and self.exam_part not in ["Part 1", "Part 2"]:
            raise ValueError(f"Invalid exam part: {self.exam_part}")

        # Validate task_number if present
        if self.task_number is not None and (self.task_number < 1 or self.task_number > 19):
            raise ValueError(f"Task number {self.task_number} is out of range")

        # Validate difficulty_level if present
        valid_difficulties = ["basic", "advanced"]
        if self.difficulty_level and self.difficulty_level not in valid_difficulties:
            raise ValueError(f"Invalid difficulty level: {self.difficulty_level}")

    # Identity methods required for Entities
    def __eq__(self, other):
        """Check equality based on the entity's identity (problem_id)."""
        if not isinstance(other, Problem):
            return False
        return self.problem_id == other.problem_id

    def __hash__(self):
        """Hash based on the entity's identity (problem_id)."""
        return hash(self.problem_id)

    # Domain Behavior Methods
    def is_answer_correct(self, user_answer: str) -> bool:
        """Check if a user's answer matches the stored correct answer."""
        if self.answer is None:
            return False
        return self.answer.strip().lower() == user_answer.strip().lower()

    def can_be_attempted(self) -> bool:
        """Check if the problem can be presented to a user for solving."""
        return bool(self.text.strip())

    def has_images(self) -> bool:
        """Check if the problem has associated images."""
        return len(self.images) > 0

    def get_total_assets_count(self) -> int:
        """Calculate the total number of images and files associated with the problem."""
        return len(self.images) + len(self.files)

    def has_files(self) -> bool:
        """Check if the problem has associated files."""
        return len(self.files) > 0

    def is_suitable_for_level(self, required_level: str) -> bool:
        """Check if the problem's difficulty matches a required level."""
        if self.difficulty_level is None:
            return False
        return self.difficulty_level == required_level
