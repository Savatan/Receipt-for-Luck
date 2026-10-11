from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods
from django.core.paginator import Paginator

from .forms import ReceiptForm
from .models import Receipt


def home(request):
    if request.user.is_authenticated:
        return redirect("receipt_create")
    return redirect("login")


def wants_json(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get("accept", "")


@login_required
@require_http_methods(["GET", "POST"])
def receipt_create(request):
    if request.method == "POST":
        form = ReceiptForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    receipt = form.save(commit=False)
                    receipt.user = request.user
                    
                    receipt.status = Receipt.Status.PENDING
                    receipt.save()
            except IntegrityError:
                form.add_error(None, "Этот чек уже зарегистрирован.")
            else:
                if wants_json(request):
                    return JsonResponse({"ok": True, "message": "Чек зарегистрирован и отправлен на проверку.", "receipt_id": receipt.pk, "account_url": reverse("receipt_list")}, status=201)
                messages.success(request, "Чек зарегистрирован и отправлен на проверку.")
                return redirect("receipt_list")
        if wants_json(request):
            return JsonResponse({"ok": False, "message": "Проверьте заполнение формы.", "errors": form.errors.get_json_data()}, status=400)
    else:
        form = ReceiptForm()
    return render(request, "receipts/receipt_form.html", {"form": form})


@login_required
@require_GET
def receipt_list(request):
    receipts = Receipt.objects.filter(user=request.user).order_by("-registered_at", "-pk")
    page = Paginator(receipts, 10).get_page(request.GET.get("page"))
    return render(request, "receipts/receipt_list.html", {"page_obj": page, "receipts": page.object_list})


def receipt_json(receipt):
    return {
        "id": receipt.pk,
        "fn": receipt.fn,
        "fd": receipt.fd,
        "fp": receipt.fp,
        "purchase_at": timezone.localtime(receipt.purchase_at).isoformat(),
        "amount": str(receipt.amount),
        "status": receipt.status,
        "status_display": receipt.get_status_display(),
        "rejection_reason": receipt.rejection_reason,
        "registered_at": timezone.localtime(receipt.registered_at).isoformat(),
    }


@require_GET
def receipt_api(request):
    
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Требуется вход в аккаунт."}, status=401)
    rows = Receipt.objects.filter(user=request.user).order_by("-registered_at", "-pk")
    response = JsonResponse({"results": [receipt_json(receipt) for receipt in rows]})
    response["Cache-Control"] = "no-store"
    return response


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("receipt_create")
    form = UserCreationForm(request.POST or None)
    for field in form.fields.values():
        field.widget.attrs["class"] = "form-control"
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("receipt_create")
    return render(request, "registration/signup.html", {"form": form})
