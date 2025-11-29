"""
Base agent class for platform-specific crawling agents
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime


class BaseAgent(ABC):
    """
    Abstract base class for platform crawling agents

    All platform-specific agents should inherit from this class
    and implement the required methods.
    """

    def __init__(self, platform_name: str):
        """
        Initialize base agent

        Args:
            platform_name: Name of the platform (e.g., 'google', 'reddit')
        """
        self.platform_name = platform_name

    @abstractmethod
    def crawl(
        self,
        keywords: List[str],
        detail: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Crawl the platform for issues matching the given criteria

        Args:
            keywords: List of keywords to search for
            detail: Additional detail for filtering

        Returns:
            List of crawled items, each containing:
                - title: str
                - url: str
                - content: str
                - platform: str
        """
        pass

    @abstractmethod
    def is_supported_domain(self, domain: str) -> bool:
        """
        Check if the given domain is supported by this agent

        Args:
            domain: Domain URL to check

        Returns:
            True if domain is supported, False otherwise
        """
        pass

    def get_platform_name(self) -> str:
        """Get the platform name"""
        return self.platform_name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(platform='{self.platform_name}')"
