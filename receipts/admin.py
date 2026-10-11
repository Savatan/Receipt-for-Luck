import csv

from django.contrib import admin
from django.http import HttpResponse

from .forms import ReceiptModerationForm
from .models import Receipt


@admin.action(description="Выгрузить принятые чеки в CSV")
def export_accepted_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="accepted-receipts.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["ФН", "ФД", "ФП", "Дата покупки", "Сумма, ₽", "Пользователь", "Дата регистрации"])
    for receipt in queryset.filter(status=Receipt.Status.ACCEPTED).select_related("user"):
        writer.writerow([receipt.fn, receipt.fd, receipt.fp, receipt.purchase_at, receipt.amount, receipt.user.get_username(), receipt.registered_at])
    return response


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    form = ReceiptModerationForm
    list_display = ("fn", "fd", "fp", "purchase_at", "amount", "status", "user", "registered_at")
    list_filter = ("status", "registered_at")
    search_fields = ("fn", "fd", "fp", "user__username", "user__email")
    readonly_fields = ("registered_at",)
    ordering = ("-registered_at",)
    actions = (export_accepted_csv,)
