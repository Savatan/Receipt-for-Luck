from django import forms
from django.conf import settings
from django.utils import timezone

from .models import Receipt


class RubleAmountField(forms.DecimalField):
    def to_python(self, value):
        if isinstance(value, str):
            value = value.replace("\u00a0", "").replace(" ", "").replace(",", ".")
        return super().to_python(value)


class ReceiptForm(forms.ModelForm):
    amount = RubleAmountField(
        min_value=1000,
        max_digits=10,
        decimal_places=2,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off"}),
        label="Сумма, ₽",
    )

    class Meta:
        model = Receipt
        fields = ("fn", "fd", "fp", "purchase_at", "amount")
        widgets = {
            "fn": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off", "maxlength": 32}),
            "fd": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off", "maxlength": 32}),
            "fp": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off", "maxlength": 32}),
            "purchase_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["purchase_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            field.widget.attrs["data-field"] = name

    def clean_purchase_at(self):
        purchase_at = self.cleaned_data["purchase_at"]
        
        
        if timezone.is_naive(purchase_at):
            purchase_at = timezone.make_aware(purchase_at, timezone.get_default_timezone())
        local_day = timezone.localtime(purchase_at, timezone.get_default_timezone()).date()
        if not (settings.CAMPAIGN_START_DATE <= local_day <= settings.CAMPAIGN_END_DATE):
            start = settings.CAMPAIGN_START_DATE.strftime("%d.%m.%Y")
            end = settings.CAMPAIGN_END_DATE.strftime("%d.%m.%Y")
            raise forms.ValidationError(f"Дата покупки должна быть с {start} по {end} включительно.")
        return purchase_at

    def clean(self):
        cleaned = super().clean()
        identifiers = (cleaned.get("fn"), cleaned.get("fd"), cleaned.get("fp"))
        if all(identifiers) and Receipt.objects.filter(fn=identifiers[0], fd=identifiers[1], fp=identifiers[2]).exists():
            raise forms.ValidationError("Этот чек уже зарегистрирован.")
        return cleaned


class ReceiptModerationForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == Receipt.Status.REJECTED and not (cleaned.get("rejection_reason") or "").strip():
            self.add_error("rejection_reason", "Укажите причину отказа.")
        return cleaned
