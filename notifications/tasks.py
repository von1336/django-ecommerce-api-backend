import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation(order_id):
    logger.info("Order confirmation sent for order %s", order_id)


@shared_task
def send_order_status_update(order_id, new_status):
    logger.info("Order status update sent for order %s: %s", order_id, new_status)


@shared_task
def generate_daily_sales_report():
    from orders.models import Order

    since = timezone.now() - timedelta(hours=24)
    orders = Order.objects.filter(created_at__gte=since).exclude(status="cancelled")
    total = sum(o.total_amount for o in orders)
    count = orders.count()
    logger.info(
        "Daily sales report: %s orders, total amount: %s",
        count,
        total,
    )
