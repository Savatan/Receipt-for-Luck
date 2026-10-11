
import django.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Receipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fn", models.CharField(max_length=32, validators=[django.core.validators.RegexValidator("^\\d+$", "Укажите только цифры.")], verbose_name="ФН")),
                ("fd", models.CharField(max_length=32, validators=[django.core.validators.RegexValidator("^\\d+$", "Укажите только цифры.")], verbose_name="ФД")),
                ("fp", models.CharField(max_length=32, validators=[django.core.validators.RegexValidator("^\\d+$", "Укажите только цифры.")], verbose_name="ФП")),
                ("purchase_at", models.DateTimeField(verbose_name="Дата и время покупки")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(1000)], verbose_name="Сумма, ₽")),
                ("status", models.CharField(choices=[("pending", "На проверке"), ("accepted", "Принят"), ("rejected", "Отклонён")], default="pending", max_length=16, verbose_name="Статус")),
                ("rejection_reason", models.TextField(blank=True, verbose_name="Причина отказа")),
                ("registered_at", models.DateTimeField(auto_now_add=True, verbose_name="Зарегистрирован")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="receipts", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={"verbose_name": "чек", "verbose_name_plural": "чеки", "ordering": ["-registered_at", "-pk"]},
        ),
        migrations.AddConstraint(
            model_name="receipt",
            constraint=models.UniqueConstraint(fields=("fn", "fd", "fp"), name="unique_fiscal_receipt"),
        ),
    ]
