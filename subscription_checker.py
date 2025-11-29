#!/usr/bin/env python3
"""
Subscription Checker - Check subscriptions at scheduled times and send emails

This script runs continuously and checks subscriptions based on their notification_time.
"""
import os
import time
import redis
import json
from pathlib import Path
from datetime import datetime, timedelta
import schedule

# Load environment variables
try:
    from dotenv import load_dotenv
    dotenv_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path)
except ImportError:
    pass

from models.user_form import UserForm
from controller import ControllerAgent
from utils.logger import setup_logger
from email_sender import send_notification_email

# Redis connection
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

logger = setup_logger()

def get_all_subscriptions():
    """Get all active subscriptions"""
    all_subs = []
    try:
        for key in redis_client.scan_iter("subscription:*"):
            # Skip the email set keys
            if ":subscriptions" in key:
                continue
            
            data = redis_client.get(key)
            if data:
                sub = json.loads(data)
                if sub.get('active', True):
                    all_subs.append(sub)
    except Exception as e:
        logger.error(f"[CHECKER] Error getting subscriptions: {e}")
    
    return all_subs

def check_subscription(subscription):
    """
    Check a subscription for new results and send email if found

    Returns:
        int: Number of new results found
    """
    logger.info(f"[CHECKER] Checking subscription {subscription['subscription_id']} for {subscription['email']}")

    try:
        # Create UserForm from subscription
        user_form = UserForm(
            keywords=subscription['keywords'],
            platforms=subscription['platforms'],
            detail=subscription.get('detail', '')
        )

        # Run controller
        controller = ControllerAgent()
        results = controller.run(user_form)

        # Get new results from filtered results
        new_results = []
        total_new = 0

        if results and results.get('results_by_platform'):
            for platform, items in results['results_by_platform'].items():
                for item in items:
                    new_results.append(item)
                    total_new += 1

        logger.info(f"[CHECKER] Found {total_new} results for subscription {subscription['subscription_id']}")

        # Send email if there are results
        if total_new > 0:
            success = send_notification_email(
                recipient_email=subscription['email'],
                keywords=subscription['keywords'],
                platforms=subscription['platforms'],
                new_results=new_results[:10],  # Send top 10
                total_new=total_new
            )

            if success:
                logger.info(f"[CHECKER] Email sent successfully to {subscription['email']}")
            else:
                logger.error(f"[CHECKER] Failed to send email to {subscription['email']}")

        # Update last_checked timestamp
        import hashlib
        email = subscription['email']
        sub_id = subscription['subscription_id']
        key = f"subscription:{email}:{sub_id}"
        
        subscription['last_checked'] = time.time()
        redis_client.set(key, json.dumps(subscription, ensure_ascii=False))

        return total_new

    except Exception as e:
        logger.error(f"[CHECKER] Error checking subscription {subscription['subscription_id']}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def check_subscriptions_for_time(notification_time):
    """Check all subscriptions with the given notification time"""
    logger.info(f"[CHECKER] Checking subscriptions for time: {notification_time}")
    
    subscriptions = get_all_subscriptions()
    matching_subs = [s for s in subscriptions if s.get('notification_time') == notification_time]
    
    logger.info(f"[CHECKER] Found {len(matching_subs)} subscriptions for {notification_time}")
    
    for subscription in matching_subs:
        try:
            new_count = check_subscription(subscription)
            logger.info(f"[CHECKER] Subscription {subscription['subscription_id']}: {new_count} new results")
        except Exception as e:
            logger.error(f"[CHECKER] Error processing subscription: {e}")
            continue

def schedule_all_subscriptions():
    """Schedule checks for all subscriptions based on their notification_time"""
    subscriptions = get_all_subscriptions()
    
    # Get unique notification times
    notification_times = set(s.get('notification_time', '09:00') for s in subscriptions)
    
    logger.info(f"[CHECKER] Scheduling checks for {len(notification_times)} different times")
    
    # Clear existing schedule
    schedule.clear()
    
    # Schedule each time
    for notif_time in notification_times:
        schedule.every().day.at(notif_time).do(check_subscriptions_for_time, notif_time)
        logger.info(f"[CHECKER] Scheduled daily check at {notif_time}")

def run_scheduler():
    """Main scheduler loop"""
    logger.info("[CHECKER] Starting subscription checker scheduler...")
    
    # Initial scheduling
    schedule_all_subscriptions()
    
    # Re-schedule every hour to pick up new subscriptions
    schedule.every().hour.do(schedule_all_subscriptions)
    
    logger.info("[CHECKER] Scheduler started. Waiting for scheduled times...")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("[CHECKER] Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"[CHECKER] Unexpected error in scheduler loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
