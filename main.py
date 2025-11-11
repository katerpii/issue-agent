#!/usr/bin/env python3
"""
Issue Agent - Main Entry Point

AI agent-based personalized issue notification system
"""
import sys
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    dotenv_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path)
except ImportError:
    # python-dotenv not installed, environment variables must be set manually
    pass

from models.user_form import UserForm
from controller import ControllerAgent
from config.settings import Settings
from utils.logger import setup_logger, log_results


def print_banner():
    """Print application banner"""
    banner = """
    TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW
    Q                                                       Q
    Q              ISSUE AGENT SYSTEM v0.1                  Q
    Q                                                       Q
    Q    AI-Powered Personalized Issue Notification        Q
    Q                                                       Q
    ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]
    """
    print(banner)


def print_available_platforms(controller: ControllerAgent):
    """Print available platforms"""
    platforms = controller.get_available_platforms()
    print(f"\nAvailable platforms: {', '.join(platforms)}")
    print()


def main():
    """Main execution function"""
    # Setup logger
    logger = setup_logger()

    try:
        # Print banner
        print_banner()

        # Initialize controller agent
        controller = ControllerAgent()
        logger.info(f"Initialized: {controller}")

        # Show available platforms
        print_available_platforms(controller)

        # Get user input
        try:
            user_form = UserForm.from_input()
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error collecting user input: {e}")
            sys.exit(1)

        # Execute controller agent (Pipeline Step 1)
        logger.info("\nStarting pipeline...")
        results = controller.run(user_form)

        # Display results
        print("\n" + "=" * 50)
        print("RESULTS")
        print("=" * 50)

        if results:
            log_results(logger, results)
        else:
            logger.warning("No results found.")

        print("\n" + "=" * 50)
        logger.info("Pipeline execution completed successfully!")
        print("=" * 50 + "\n")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
