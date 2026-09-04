from decimal import Decimal

from django.db import models

from catalog.models import Product
from users.models import User


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart",
    )
    session_key = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        pass

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Cart (session: {self.session_key})"

    @property
    def total_price(self):
        return sum(item.item_total for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("cart", "product")]
        ordering = ["added_at"]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def item_total(self):
        return self.product.price * self.quantity
