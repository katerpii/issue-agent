# #!/usr/bin/env python3
# """
# Subscription Checker - Background job to check subscriptions periodically

# This script runs as a separate background process and checks all active
# subscriptions for new results every hour.
# """
# import os
# import time
# import redis
# import json
# from pathlib import Path
# from datetime import datetime

# # Load environment variables
# try:
#     from dotenv import load_dotenv
#     dotenv_path = Path(__file__).parent / '.env'
#     load_dotenv(dotenv_path)
# except ImportError:
#     pass

# from models.user_form import UserForm
# from controller import ControllerAgent
# from utils.logger import setup_logger

# # Redis connection
# redis_host = os.getenv("REDIS_HOST", "localhost")
# redis_port = int(os.getenv("REDIS_PORT", 6379))
# redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

# logger = setup_logger()

# def get_all_active_subscriptions():
#     """Get all active subscriptions"""
#     all_subs = []
#     for key in redis_client.scan_iter("subscription:*"):
#         data = redis_client.get(key)
#         if data:
#             sub = json.loads(data)
#             if sub.get('active', True):
#                 all_subs.append(sub)
#     return all_subs

# def check_subscription(subscription):
#     """
#     Check a subscription for new results

#     Returns:
#         tuple: (new_results_count, filtered_results)
#     """
#     logger.info(f"[CHECKER] Checking subscription {subscription['subscription_id']} for user {subscription['user_id']}")

#     try:
#         # Create UserForm from subscription
#         user_form = UserForm(
#             keywords=subscription['keywords'],
#             platforms=subscription['platforms'],
#             detail=subscription.get('detail', '')
#         )

#         # Run controller
#         controller = ControllerAgent()
#         results = controller.run(user_form)

#         # Check for new results (not seen before)
#         new_results = []
#         total_new = 0

#         if results and results.get('results_by_platform'):
#             for platform, items in results['results_by_platform'].items():
#                 for item in items:
#                     url = item.get('url', '')
#                     if not url:
#                         continue

#                     # Check if this is a NEW result (not in Redis yet)
#                     import hashlib
#                     url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
#                     key = f"result:{platform}:{url_hash}"

#                     if not redis_client.exists(key):
#                         new_results.append(item)
#                         total_new += 1

#         logger.info(f"[CHECKER] Found {total_new} new results for subscription {subscription['subscription_id']}")

#         # Update last_checked timestamp
#         sub_key = f"subscription:{subscription['user_id']}:{subscription['subscription_id']}"
#         sub_data = redis_client.get(sub_key)
#         if sub_data:
#             sub = json.loads(sub_data)
#             sub['last_checked'] = time.time()
#             redis_client.set(sub_key, json.dumps(sub, ensure_ascii=False))

#         # Store notification if there are new results
#         if total_new > 0:
#             notification = {
#                 'subscription_id': subscription['subscription_id'],
#                 'user_id': subscription['user_id'],
#                 'new_results_count': total_new,
#                 'results': new_results[:10],  # Limit to 10 results
#                 'timestamp': time.time(),
#                 'keywords': subscription['keywords'],
#                 'platforms': subscription['platforms']
#             }

#             # Store notification in Redis
#             notif_key = f"notification:{subscription['user_id']}:{int(time.time())}"
#             redis_client.setex(notif_key, 7 * 24 * 60 * 60, json.dumps(notification, ensure_ascii=False))  # 7 days TTL

#             # Add to user's notification queue
#             redis_client.lpush(f"notifications:{subscription['user_id']}", notif_key)
#             redis_client.ltrim(f"notifications:{subscription['user_id']}", 0, 99)  # Keep last 100 notifications

#             logger.info(f"[CHECKER] Created notification for user {subscription['user_id']}")

#         return total_new, new_results

#     except Exception as e:
#         logger.error(f"[CHECKER] Error checking subscription {subscription['subscription_id']}: {e}")
#         import traceback
#         traceback.print_exc()
#         return 0, []

# def run_checker_loop(check_interval_minutes=60):
#     """
#     Main loop that checks all subscriptions periodically

#     Args:
#         check_interval_minutes: How often to check (default: 60 minutes)
#     """
#     logger.info(f"[CHECKER] Starting subscription checker (interval: {check_interval_minutes} minutes)")

#     while True:
#         try:
#             logger.info("[CHECKER] Starting subscription check cycle...")

#             subscriptions = get_all_active_subscriptions()
#             logger.info(f"[CHECKER] Found {len(subscriptions)} active subscriptions")

#             for subscription in subscriptions:
#                 try:
#                     new_count, _ = check_subscription(subscription)
#                     logger.info(f"[CHECKER] Subscription {subscription['subscription_id']}: {new_count} new results")

#                 except Exception as e:
#                     logger.error(f"[CHECKER] Error processing subscription: {e}")
#                     continue

#                 # Small delay between subscriptions to avoid overwhelming the system
#                 time.sleep(5)

#             logger.info(f"[CHECKER] Cycle complete. Sleeping for {check_interval_minutes} minutes...")
#             time.sleep(check_interval_minutes * 60)

#         except KeyboardInterrupt:
#             logger.info("[CHECKER] Received interrupt signal, shutting down...")
#             break
#         except Exception as e:
#             logger.error(f"[CHECKER] Unexpected error in main loop: {e}")
#             import traceback
#             traceback.print_exc()
#             time.sleep(60)  # Wait 1 minute before retrying

# if __name__ == "__main__":
#     # For testing: run every 5 minutes
#     # For production: run every 60 minutes
#     check_interval = int(os.getenv("SUBSCRIPTION_CHECK_INTERVAL", "60"))
#     run_checker_loop(check_interval_minutes=check_interval)
