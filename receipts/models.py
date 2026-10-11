from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

digits_only = RegexValidator(r"^\d+$", "Укажите только цифры.")


class Receipt(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "На проверке"
        ACCEPTED = "accepted", "Принят"
        REJECTED = "rejected", "Отклонён"

    fn = models.CharField("ФН", max_length=32, validators=[digits_only])
    fd = models.CharField("ФД", max_length=32, validators=[digits_only])
    fp = models.CharField("ФП", max_length=32, validators=[digits_only])
    purchase_at = models.DateTimeField("Дата и время покупки")
    amount = models.DecimalField("Сумма, ₽", max_digits=10, decimal_places=2, validators=[MinValueValidator(1000)])
    status = models.CharField("Статус", max_length=16, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField("Причина отказа", blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="receipts", verbose_name="Пользователь")
    registered_at = models.DateTimeField("Зарегистрирован", auto_now_add=True)

    class Meta:
        ordering = ["-registered_at", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["fn", "fd", "fp"], name="unique_fiscal_receipt"),
        ]
        indexes = [
            models.Index(fields=["user", "-registered_at"], name="receipt_user_registered_idx"),
        ]
        verbose_name = "чек"
        verbose_name_plural = "чеки"

    def clean(self):
        super().clean()
        if self.status == self.Status.REJECTED and not self.rejection_reason.strip():
            raise ValidationError({"rejection_reason": "Укажите причину отказа."})

    def __str__(self):
        return f"Чек {self.fn}/{self.fd} — {self.get_status_display()}"
