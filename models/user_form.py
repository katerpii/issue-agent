"""
User form model for collecting user preferences
"""
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, field_validator, model_validator


@dataclass
class UserForm:
    """
    User input form for issue notification preferences

    Attributes:
        keywords: List of keywords to search for
        platforms: List of platform names (e.g., 'google', 'reddit')
        start_date: Start date for search period
        end_date: End date for search period
        detail: Additional detail/description for personalized filtering
    """
    keywords: List[str]
    platforms: List[str]
    start_date: datetime
    end_date: datetime
    detail: str

    def __post_init__(self):
        """Validate user form data"""
        if not self.keywords:
            raise ValueError("At least one keyword is required")

        if not self.platforms:
            raise ValueError("At least one platform is required")

        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date")

    @classmethod
    def from_input(cls) -> 'UserForm':
        """
        Create UserForm instance from user input

        Returns:
            UserForm instance with validated data
        """
        print("=" * 50)
        print("Issue Agent - User Form")
        print("=" * 50)

        # Collect keywords
        keywords_input = input("Keywords (comma-separated): ").strip()
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

        # Collect platforms
        platforms_input = input("Platforms (comma-separated, e.g., google,reddit): ").strip()
        platforms = [p.strip().lower() for p in platforms_input.split(",") if p.strip()]

        # Collect dates
        start_date_str = input("Start date (YYYY-MM-DD): ").strip()
        end_date_str = input("End date (YYYY-MM-DD): ").strip()

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")

        # Collect detail
        detail = input("Detail (additional preferences): ").strip()

        return cls(
            keywords=keywords,
            platforms=platforms,
            start_date=start_date,
            end_date=end_date,
            detail=detail
        )

    def to_dict(self) -> dict:
        """Convert UserForm to dictionary"""
        return {
            'keywords': self.keywords,
            'platforms': self.platforms,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'detail': self.detail
        }

    def __str__(self) -> str:
        """String representation of UserForm"""
        return (
            f"UserForm(\n"
            f"  Keywords: {', '.join(self.keywords)}\n"
            f"  Platforms: {', '.join(self.platforms)}\n"
            f"  Period: {self.start_date.date()} ~ {self.end_date.date()}\n"
            f"  Detail: {self.detail}\n"
            f")"
        )


# --- Pydantic Model for API ---
class UserFormAPI(BaseModel):
    """
    Pydantic model for API request body validation
    """
    keywords: List[str]
    platforms: List[str]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    detail: str

    @field_validator('keywords', 'platforms')
    def check_not_empty(cls, v):
        if not v:
            raise ValueError("must not be empty")
        return v

    @model_validator(mode='after')
    def check_dates(self) -> 'UserFormAPI':
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        return self
