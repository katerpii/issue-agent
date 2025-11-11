"""
Logging utility for the Issue Agent system
"""
import logging
import sys
from datetime import datetime


def setup_logger(name: str = "IssueAgent", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure logger

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def log_user_form(logger: logging.Logger, user_form):
    """
    Log user form details

    Args:
        logger: Logger instance
        user_form: UserForm instance
    """
    logger.info("=" * 50)
    logger.info("User Form Received")
    logger.info("=" * 50)
    logger.info(f"Keywords: {', '.join(user_form.keywords)}")
    logger.info(f"Platforms: {', '.join(user_form.platforms)}")
    logger.info(f"Period: {user_form.start_date.date()} ~ {user_form.end_date.date()}")
    logger.info(f"Detail: {user_form.detail}")
    logger.info("=" * 50)


def log_results(logger: logging.Logger, results: list):
    """
    Log crawling results

    Args:
        logger: Logger instance
        results: List of results
    """
    logger.info("=" * 50)
    logger.info(f"Total Results: {len(results)}")
    logger.info("=" * 50)

    for i, result in enumerate(results, 1):
        logger.info(f"\nResult {i}:")
        logger.info(f"  Platform: {result.get('platform', 'N/A')}")
        logger.info(f"  Title: {result.get('title', 'N/A')}")
        logger.info(f"  URL: {result.get('url', 'N/A')}")
        logger.info(f"  Date: {result.get('date', 'N/A')}")
