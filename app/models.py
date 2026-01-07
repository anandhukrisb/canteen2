from django.db import models
from django.contrib.auth.models import User
import uuid

# --------------------------------------------------
# CANTEEN MODEL
# --------------------------------------------------
# Represents a food court / canteen.
# --------------------------------------------------

class Canteen(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# --------------------------------------------------
# LAB MODEL
# --------------------------------------------------
# Represents a lab / hall.
# Orders from this lab go to ONE canteen.
# --------------------------------------------------

class Lab(models.Model):
    name = models.CharField(max_length=100)
    canteen = models.ForeignKey(
        Canteen,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.name} → {self.canteen.name}"


# --------------------------------------------------
# SEAT MODEL
# --------------------------------------------------
# Represents an individual seat inside a lab.
# --------------------------------------------------

class Seat(models.Model):
    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE
    )
    seat_number = models.CharField(max_length=20)

    class Meta:
        unique_together = ('lab', 'seat_number')

    def __str__(self):
        return f"{self.lab.name} - Seat {self.seat_number}"


# --------------------------------------------------
# QR CODE MODEL
# --------------------------------------------------
# One QR per seat.
# QR scan identifies Seat → Lab → Canteen.
# --------------------------------------------------

# models.py

class QRCode(models.Model):
    seat = models.OneToOneField(
        Seat,
        on_delete=models.CASCADE
    )
    qr_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    qr_image = models.ImageField(
        upload_to="qr_codes/",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"QR for {self.seat}"



# --------------------------------------------------
# MENU ITEM MODEL
# --------------------------------------------------
# Represents deliverable items.
# No pricing — hospitality-based system.
# --------------------------------------------------

class MenuItem(models.Model):
    canteen = models.ForeignKey(
        Canteen,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.canteen.name})"


class ItemOption(models.Model):
    """
    Single selectable option for a menu item
    (eg: Sugar / No Sugar)
    """
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="options"
    )
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.menu_item.name})"


# --------------------------------------------------
# ORDER MODEL
# --------------------------------------------------
# Simple delivery order.
# Only NEW and DELIVERED states.
# --------------------------------------------------

from django.core.exceptions import ValidationError
from django.db import models
import uuid

class Order(models.Model):

    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('DELIVERED', 'Delivered'),
    )

    order_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)

    option = models.ForeignKey(
        ItemOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional single selection (eg: No Sugar)"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='NEW'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    
    def clean(self):
        if self.option and self.option.menu_item != self.item:
            raise ValidationError(
                {"option": "Selected option does not belong to the selected menu item."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # Enforces clean() every time
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} → {self.seat}"



# -----------------------------
# CANTEEN MANAGER
# -----------------------------
class CanteenManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} → {self.canteen.name}"