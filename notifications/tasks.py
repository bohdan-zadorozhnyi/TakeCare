import logging
from datetime import timedelta
from django.utils import timezone
from .services import NotificationService
from .models import Notification
import time

logger = logging.getLogger(__name__)

def retry_failed_notifications():
    """
    Retry sending notifications that failed to deliver
    
    This task should be scheduled to run periodically
    """
    logger.info("Starting scheduled task to retry failed notifications")
    start_time = time.time()
    
    retry_count = NotificationService.retry_failed_deliveries(
        max_retries=5,  # Try up to 5 times
        max_age_hours=24  # Only retry notifications less than 24 hours old
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Completed notification retry task in {duration:.2f}s. Retried {retry_count} notifications")

def cleanup_old_notifications():
    """
    Delete or archive old notifications
    
    This task should be scheduled to run periodically (e.g., daily)
    """
    # Automatically delete notifications older than 90 days
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count = Notification.objects.filter(date__lt=cutoff_date).delete()
    
    logger.info(f"Deleted {deleted_count} old notifications older than 90 days")
