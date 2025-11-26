"""
User form model for collecting user preferences
"""
from typing import List, Optional
from pydantic import BaseModel, field_validator
from dataclasses import dataclass


@dataclass
class UserForm:
    """
    User input form for issue notification preferences

    Attributes:
        keywords: List of keywords to search for
        platforms: List of platform names (e.g., 'google', 'reddit')
        detail: Additional detail/description for personalized filtering
    """
    keywords: List[str]
    platforms: List[str]
    detail: str

    def __post_init__(self):
        """Validate user form data"""
        if not self.keywords:
            raise ValueError("At least one keyword is required")

        if not self.platforms:
            raise ValueError("At least one platform is required")

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

        # Collect detail
        detail = input("Detail (additional preferences): ").strip()

        return cls(
            keywords=keywords,
            platforms=platforms,
            detail=detail
        )

    def to_dict(self) -> dict:
        """Convert UserForm to dictionary"""
        return {
            'keywords': self.keywords,
            'platforms': self.platforms,
            'detail': self.detail
        }

    def __str__(self) -> str:
        """String representation of UserForm"""
        return (
            f"UserForm(\n"
            f"  Keywords: {', '.join(self.keywords)}\n"
            f"  Platforms: {', '.join(self.platforms)}\n"
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
    detail: str

    @field_validator('keywords', 'platforms')
    def check_not_empty(cls, v):
        if not v:
            raise ValueError("must not be empty")
        return v
