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

# ----------------------------------------------------------------------
# --- FastAPI Web Server Code (Added for Docker Web Interface) ---
# ----------------------------------------------------------------------

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPI 애플리케이션 초기화
app = FastAPI(title="Issue Agent API")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용으로 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis 클라이언트 초기화
try:
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    # Redis 연결 테스트
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Error connecting to Redis: {e}")
    redis_client = None

# 루트 엔드포인트
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Issue Agent API!"}

# 방문 횟수 API 엔드포인트
@app.get("/api/visit")
async def increment_visit_count():
    if not redis_client:
        return {"error": "Redis connection not available"}, 500
    try:
        visit_count = redis_client.incr("visits")
        return {"visits": visit_count}
    except Exception as e:
        return {"error": f"An error occurred with Redis: {e}"}, 500
