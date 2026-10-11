from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("receipts", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="receipt",
            index=models.Index(fields=["user", "-registered_at"], name="receipt_user_registered_idx"),
        ),
    ]
