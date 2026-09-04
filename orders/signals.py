from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.tasks import send_order_confirmation, send_order_status_update

from .models import Order


@receiver(post_save, sender=Order)
def on_order_save(sender, instance, created, **kwargs):
    if created:
        send_order_confirmation.delay(instance.id)
    else:
        send_order_status_update.delay(instance.id, instance.status)
        if instance.status == Order.Status.CONFIRMED:
            send_order_confirmation.delay(instance.id)
