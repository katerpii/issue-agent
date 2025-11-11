"""
Configuration settings for the Issue Agent system
"""
import os
from pathlib import Path


class Settings:
    """Application settings and configuration"""

    # Project paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    AGENTS_DIR = BASE_DIR / "agents"

    # Domain configuration
    DOMAINS_FILE = DATA_DIR / "domains.txt"

    # Agent configuration
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RESULTS_PER_PLATFORM = 100

    # Filtering configuration
    FILTER_THRESHOLD = 5  # Maximum results before LLM filtering

    @classmethod
    def load_supported_domains(cls) -> list:
        """
        Load supported domains from domains.txt

        Returns:
            List of supported domain URLs
        """
        domains = []

        if not cls.DOMAINS_FILE.exists():
            return domains

        with open(cls.DOMAINS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    domains.append(line)

        return domains

    @classmethod
    def is_domain_supported(cls, domain: str) -> bool:
        """
        Check if a domain is supported

        Args:
            domain: Domain URL to check

        Returns:
            True if domain is supported, False otherwise
        """
        supported_domains = cls.load_supported_domains()
        return any(domain.startswith(supported) for supported in supported_domains)

    @classmethod
    def get_config_summary(cls) -> str:
        """Get a summary of current configuration"""
        return f"""
Issue Agent Configuration
-------------------------
Base Directory: {cls.BASE_DIR}
Data Directory: {cls.DATA_DIR}
Agents Directory: {cls.AGENTS_DIR}
Domains File: {cls.DOMAINS_FILE}
Default Timeout: {cls.DEFAULT_TIMEOUT}s
Max Results Per Platform: {cls.MAX_RESULTS_PER_PLATFORM}
Filter Threshold: {cls.FILTER_THRESHOLD}
        """.strip()
