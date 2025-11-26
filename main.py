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
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, time
import json

# FastAPI 애플리케이션 초기화
app = FastAPI(title="Issue Agent API")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Log detailed validation errors.
    """
    logger = setup_logger()
    error_details = exc.errors()
    logger.error(f"Validation error for request to {request.url}: {json.dumps(error_details, indent=2)}")
    return JSONResponse(
        status_code=422,
        content={"detail": error_details},
    )

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

# 이슈 에이전트 실행 엔드포인트
@app.post("/api/run")
async def run_issue_agent(form_data: UserFormAPI):
    """
    Run the issue agent with the provided form data.
    """
    logger = setup_logger()
    try:
        # Pydantic 모델(UserFormAPI)을 dataclass(UserForm)로 변환
        user_form = UserForm(
            keywords=form_data.keywords,
            platforms=form_data.platforms,
            start_date=datetime.combine(form_data.start_date, time.min),
            end_date=datetime.combine(form_data.end_date, time.max),
            detail=form_data.detail
        )

        # 컨트롤러 에이전트 초기화 및 실행
        controller = ControllerAgent()
        logger.info(f"Initialized: {controller}")
        
        results = controller.run(user_form)
        
        logger.info("Pipeline execution completed successfully!")
        
        return {"results": results}

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in /api/run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
