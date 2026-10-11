from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import ReceiptForm
from .models import Receipt


@override_settings(CAMPAIGN_START_DATE=date(2026, 1, 1), CAMPAIGN_END_DATE=date(2026, 12, 31))
class ReceiptValidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="buyer", password="safe-pass-123")

    def payload(self, **overrides):
        data = {"fn": "123456789012", "fd": "98765", "fp": "4567890123", "purchase_at": "2026-06-20T12:30", "amount": "1000.00"}
        data.update(overrides)
        return data

    def test_minimum_amount_is_accepted_and_new_receipt_is_pending(self):
        form = ReceiptForm(self.payload())
        self.assertTrue(form.is_valid(), form.errors)
        receipt = form.save(commit=False)
        receipt.user = self.user
        receipt.save()
        self.assertEqual(receipt.status, Receipt.Status.PENDING)

    def test_amount_below_minimum_is_rejected(self):
        form = ReceiptForm(self.payload(amount="999.99"))
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_receipt_outside_campaign_period_is_rejected(self):
        form = ReceiptForm(self.payload(purchase_at="2025-12-31T23:59"))
        self.assertFalse(form.is_valid())
        self.assertIn("purchase_at", form.errors)

    def test_non_digit_fiscal_number_is_rejected(self):
        form = ReceiptForm(self.payload(fn="12A45"))
        self.assertFalse(form.is_valid())
        self.assertIn("fn", form.errors)

    def test_duplicate_fiscal_tuple_is_rejected(self):
        Receipt.objects.create(user=self.user, **{
            "fn": "123456789012", "fd": "98765", "fp": "4567890123",
            "purchase_at": "2026-06-20T12:30+03:00", "amount": "1000.00",
        })
        form = ReceiptForm(self.payload())
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class ReceiptApiPrivacyTests(TestCase):
    def test_api_returns_only_current_users_receipts_even_with_foreign_user_filter(self):
        user_model = get_user_model()
        owner = user_model.objects.create_user(username="owner", password="safe-pass-123")
        other = user_model.objects.create_user(username="other", password="safe-pass-123")
        own_receipt = Receipt.objects.create(user=owner, fn="1", fd="2", fp="3", purchase_at="2026-06-20T12:30+03:00", amount="1000")
        Receipt.objects.create(user=other, fn="4", fd="5", fp="6", purchase_at="2026-06-20T12:30+03:00", amount="2000")
        self.client.force_login(owner)

        response = self.client.get(reverse("receipt_api"), {"user_id": other.pk, "owner": other.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()["results"]], [own_receipt.pk])

    def test_anonymous_api_request_is_json_401(self):
        response = self.client.get(reverse("receipt_api"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Требуется вход в аккаунт.")


class ReceiptPageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="buyer", password="safe-pass-123")
        self.client.force_login(self.user)

    def test_registration_and_account_pages_render(self):
        registration = self.client.get(reverse("receipt_create"))
        account = self.client.get(reverse("receipt_list"))
        self.assertEqual(registration.status_code, 200)
        self.assertContains(registration, "Зарегистрировать чек")
        self.assertEqual(account.status_code, 200)
        self.assertContains(account, "Здесь будет история ваших чеков")

    def test_ajax_registration_saves_pending_receipt_and_returns_json(self):
        response = self.client.post(
            reverse("receipt_create"),
            {"fn": "111", "fd": "222", "fp": "333", "purchase_at": "2026-06-20T12:30", "amount": "1 000,00"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(Receipt.objects.get().status, Receipt.Status.PENDING)

    def test_account_table_renders_receipt_status_and_reason(self):
        Receipt.objects.create(
            user=self.user,
            fn="111",
            fd="222",
            fp="333",
            purchase_at="2026-06-20T12:30+03:00",
            amount="12000",
            status=Receipt.Status.REJECTED,
            rejection_reason="Чек не читается",
        )
        response = self.client.get(reverse("receipt_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "История чеков")
        self.assertContains(response, "Отклонён")
        self.assertContains(response, "Чек не читается")

    def test_duplicate_ajax_submission_returns_validation_error(self):
        Receipt.objects.create(user=self.user, fn="111", fd="222", fp="333", purchase_at="2026-06-20T12:30+03:00", amount="1000")
        response = self.client.post(
            reverse("receipt_create"),
            {"fn": "111", "fd": "222", "fp": "333", "purchase_at": "2026-06-20T12:30", "amount": "1000"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("уже зарегистрирован", response.json()["errors"]["__all__"][0]["message"])
