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

from models.user_form import UserForm, UserFormAPI
from controller import ControllerAgent
from utils.logger import setup_logger, log_results
import hashlib
import json as json_lib


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

# ============================================
# Redis Helper Functions for Deduplication
# ============================================

# def get_url_hash(url: str) -> str:
#     """Generate MD5 hash for URL to use as Redis key"""
#     return hashlib.md5(url.encode('utf-8')).hexdigest()

# def is_result_seen(platform: str, url: str) -> bool:
#     """Check if a result URL has been seen before"""
#     if not redis_client:
#         return False

#     url_hash = get_url_hash(url)
#     key = f"result:{platform}:{url_hash}"
#     return redis_client.exists(key) > 0

# def store_result(platform: str, url: str, result_data: dict, expiry_days: int = 30):
#     """Store a result in Redis with expiration (default 30 days)"""
#     if not redis_client:
#         return

#     url_hash = get_url_hash(url)
#     key = f"result:{platform}:{url_hash}"

#     # Store as JSON string
#     redis_client.setex(
#         key,
#         expiry_days * 24 * 60 * 60,  # Convert days to seconds
#         json_lib.dumps(result_data, ensure_ascii=False)
#     )

# def filter_duplicate_results(results_by_platform: dict) -> tuple:
#     """
#     Filter out results that have been seen before and store new ones

#     Returns:
#         tuple: (filtered_results_dict, dedup_stats_dict)
#     """
#     filtered = {}
#     stats = {
#         'total_checked': 0,
#         'duplicates_filtered': 0,
#         'new_results': 0
#     }

#     for platform, results in results_by_platform.items():
#         filtered_results = []

#         for result in results:
#             stats['total_checked'] += 1
#             url = result.get('url', '')

#             if not url:
#                 continue

#             # Check if we've seen this URL before
#             if is_result_seen(platform, url):
#                 stats['duplicates_filtered'] += 1
#                 print(f"[DEDUP] Filtered duplicate: {url[:80]}...")
#                 continue

#             # New result - store it and include in results
#             store_result(platform, url, result)
#             filtered_results.append(result)
#             stats['new_results'] += 1

#         if filtered_results:
#             filtered[platform] = filtered_results

#     print(f"[DEDUP] Stats: {stats['total_checked']} checked, {stats['duplicates_filtered']} duplicates, {stats['new_results']} new")
#     return filtered, stats

# ============================================
# Subscription Management Functions
# ============================================

# def create_subscription(user_id: str, keywords: list, platforms: list, detail: str) -> str:
#     """
#     Create a new subscription for a user

#     Returns:
#         subscription_id: Unique ID for the subscription
#     """
#     if not redis_client:
#         return None

#     # Generate unique subscription ID
#     import time
#     subscription_id = hashlib.md5(f"{user_id}:{time.time()}".encode()).hexdigest()[:12]

#     subscription_data = {
#         'subscription_id': subscription_id,
#         'user_id': user_id,
#         'keywords': keywords,
#         'platforms': platforms,
#         'detail': detail,
#         'created_at': time.time(),
#         'last_checked': None,
#         'active': True
#     }

#     # Store subscription
#     key = f"subscription:{user_id}:{subscription_id}"
#     redis_client.set(key, json_lib.dumps(subscription_data, ensure_ascii=False))

#     # Add to user's subscription list
#     redis_client.sadd(f"user:{user_id}:subscriptions", subscription_id)

#     print(f"[SUBSCRIPTION] Created: {subscription_id} for user {user_id}")
#     return subscription_id

# def get_user_subscriptions(user_id: str) -> list:
#     """Get all subscriptions for a user"""
#     if not redis_client:
#         return []

#     subscription_ids = redis_client.smembers(f"user:{user_id}:subscriptions")
#     subscriptions = []

#     for sub_id in subscription_ids:
#         key = f"subscription:{user_id}:{sub_id}"
#         data = redis_client.get(key)
#         if data:
#             subscriptions.append(json_lib.loads(data))

#     return subscriptions

# def delete_subscription(user_id: str, subscription_id: str) -> bool:
#     """Delete a subscription"""
#     if not redis_client:
#         return False

#     key = f"subscription:{user_id}:{subscription_id}"
#     redis_client.delete(key)
#     redis_client.srem(f"user:{user_id}:subscriptions", subscription_id)

#     print(f"[SUBSCRIPTION] Deleted: {subscription_id}")
#     return True

# def get_all_active_subscriptions() -> list:
#     """Get all active subscriptions across all users (for background job)"""
#     if not redis_client:
#         return []

#     all_subs = []
#     # Find all subscription keys
#     for key in redis_client.scan_iter("subscription:*"):
#         data = redis_client.get(key)
#         if data:
#             sub = json_lib.loads(data)
#             if sub.get('active', True):
#                 all_subs.append(sub)

#     return all_subs

# def update_subscription_check_time(user_id: str, subscription_id: str):
#     """Update last_checked timestamp for a subscription"""
#     if not redis_client:
#         return

#     import time
#     key = f"subscription:{user_id}:{subscription_id}"
#     data = redis_client.get(key)

#     if data:
#         sub = json_lib.loads(data)
#         sub['last_checked'] = time.time()
#         redis_client.set(key, json_lib.dumps(sub, ensure_ascii=False))

# ============================================
# API Endpoints
# ============================================

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
            detail=form_data.detail
        )

        # 컨트롤러 에이전트 초기화 및 실행
        controller = ControllerAgent()
        logger.info(f"Initialized: {controller}")

        results = controller.run(user_form)

        logger.info("Pipeline execution completed successfully!")

        # Apply deduplication BEFORE serialization
        # if results and results.get('results_by_platform'):
        #     logger.info("Applying deduplication filter...")
        #     original_count = results.get('total_results', 0)

        #     filtered_results, dedup_stats = filter_duplicate_results(results['results_by_platform'])

        #     # Update results with deduplicated data
        #     results['results_by_platform'] = filtered_results
        #     results['total_results'] = sum(len(items) for items in filtered_results.values())
        #     results['deduplication_stats'] = dedup_stats

        #     logger.info(f"Deduplication: {original_count} -> {results['total_results']} results ({dedup_stats['duplicates_filtered']} duplicates removed)")

        #     # Update summary with dedup info
        #     if dedup_stats['duplicates_filtered'] > 0:
        #         dedup_msg = f"[{dedup_stats['new_results']} new, {dedup_stats['duplicates_filtered']} already seen] "
        #         if results.get('summary'):
        #             results['summary'] = dedup_msg + results['summary']

        # Convert datetime objects to ISO format strings for JSON serialization
        from datetime import datetime, date
        import json as json_module

        def serialize_for_json(obj):
            """Recursively serialize objects to JSON-compatible format"""
            if isinstance(obj, dict):
                return {k: serialize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_for_json(item) for item in obj]
            elif isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                # For any other type, convert to string
                return str(obj)

        try:
            serialized_results = serialize_for_json(results)

            # Test if it's actually JSON serializable
            json_module.dumps(serialized_results)

            logger.info(f"Returning results: summary={serialized_results.get('summary', '')[:100]}..., total={serialized_results.get('total_results', 0)}")

            return {"results": serialized_results}
        except Exception as e:
            logger.error(f"Failed to serialize results: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to serialize results: {str(e)}")

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in /api/run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# ============================================
# Subscription API - Email-based
# ============================================

from pydantic import BaseModel, EmailStr

class SubscriptionCreate(BaseModel):
    email: EmailStr
    notification_time: str  # HH:MM format
    keywords: list
    platforms: list
    detail: str = ""

@app.post("/api/subscriptions")
async def create_subscription_endpoint(subscription: SubscriptionCreate):
    """Create a new email-based subscription"""
    logger = setup_logger()

    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        import time

        # Generate unique subscription ID
        subscription_id = hashlib.md5(f"{subscription.email}:{time.time()}".encode()).hexdigest()[:12]

        subscription_data = {
            'subscription_id': subscription_id,
            'email': subscription.email,
            'notification_time': subscription.notification_time,
            'keywords': subscription.keywords,
            'platforms': subscription.platforms,
            'detail': subscription.detail,
            'created_at': time.time(),
            'last_checked': None,
            'active': True
        }

        # Store subscription
        key = f"subscription:{subscription.email}:{subscription_id}"
        redis_client.set(key, json_lib.dumps(subscription_data, ensure_ascii=False))

        # Add to email's subscription list
        redis_client.sadd(f"email:{subscription.email}:subscriptions", subscription_id)

        logger.info(f"Created subscription {subscription_id} for {subscription.email}")

        return {
            "subscription_id": subscription_id,
            "message": "Subscription created successfully",
            "email": subscription.email,
            "notification_time": subscription.notification_time
        }
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/subscriptions/{email}")
async def list_subscriptions_by_email(email: str):
    """Get all subscriptions for an email"""
    logger = setup_logger()

    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        subscription_ids = redis_client.smembers(f"email:{email}:subscriptions")
        subscriptions = []

        for sub_id in subscription_ids:
            key = f"subscription:{email}:{sub_id}"
            data = redis_client.get(key)
            if data:
                subscriptions.append(json_lib.loads(data))

        logger.info(f"Retrieved {len(subscriptions)} subscriptions for {email}")

        return {"subscriptions": subscriptions}
    except Exception as e:
        logger.error(f"Error retrieving subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/subscriptions/{email}/{subscription_id}")
async def delete_subscription_endpoint(email: str, subscription_id: str):
    """Delete a subscription"""
    logger = setup_logger()

    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        key = f"subscription:{email}:{subscription_id}"
        redis_client.delete(key)
        redis_client.srem(f"email:{email}:subscriptions", subscription_id)

        logger.info(f"Deleted subscription {subscription_id} for {email}")

        return {"message": "Subscription deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/subscriptions/{email}/{subscription_id}/test")
async def test_subscription_endpoint(email: str, subscription_id: str):
    """
    Manually trigger a subscription check for testing (immediate execution)
    """
    logger = setup_logger()
    logger.info(f"[TEST] Manual test triggered for subscription {subscription_id}")

    try:
        # Get subscription from Redis
        key = f"subscription:{email}:{subscription_id}"
        data = redis_client.get(key)

        if not data:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription = json_lib.loads(data)

        # Import here to avoid circular dependency
        from subscription_checker import check_subscription

        # Run subscription check immediately
        new_count = check_subscription(subscription)

        logger.info(f"[TEST] Test completed. Found {new_count} new results")

        return {
            "message": "Test completed successfully",
            "subscription_id": subscription_id,
            "email": email,
            "new_results_count": new_count,
            "keywords": subscription['keywords'],
            "platforms": subscription['platforms']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TEST] Error testing subscription: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
