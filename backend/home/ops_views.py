"""Staff workflows that extend Oscar's standard order dashboard."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from home.forms import (
    CustomOrderCreateForm,
    CustomOrderQuoteForm,
    ManualSaleForm,
    ManualSaleLineFormSet,
)
from home.models import CustomOrderInquiry
from home.services.oscar_orders import (
    InventoryUnavailable,
    create_oscar_order,
    create_order_for_custom_inquiry,
)


@staff_member_required(login_url="/dashboard/login/")
def custom_order_queue(request):
    inquiries = CustomOrderInquiry.objects.select_related("order").all()
    return render(
        request,
        "home/dashboard/custom_order_queue.html",
        {"inquiries": inquiries},
    )


@staff_member_required(login_url="/dashboard/login/")
@require_http_methods(["GET", "POST"])
@transaction.atomic
def create_in_person_custom_order(request):
    form = CustomOrderCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        inquiry = form.save(commit=False)
        inquiry.status = CustomOrderInquiry.Status.ACCEPTED
        inquiry.save()
        try:
            order = create_order_for_custom_inquiry(request, inquiry)
        except ValidationError as exc:
            inquiry.delete()
            form.add_error(None, "; ".join(exc.messages))
        else:
            messages.success(
                request,
                f"Custom order recorded as Oscar order {order.number}; invoice/payment is a later phase.",
            )
            return redirect("custom_order_detail", inquiry_id=inquiry.pk)
    return render(request, "home/dashboard/create_custom_order.html", {"form": form})


@staff_member_required(login_url="/dashboard/login/")
@require_http_methods(["GET", "POST"])
def custom_order_detail(request, inquiry_id: int):
    inquiry = get_object_or_404(
        CustomOrderInquiry.objects.select_related("order"),
        pk=inquiry_id,
    )
    form = CustomOrderQuoteForm(request.POST or None, instance=inquiry)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Custom-order notes and quote saved.")
        return redirect("custom_order_detail", inquiry_id=inquiry.pk)
    return render(
        request,
        "home/dashboard/custom_order_detail.html",
        {"inquiry": inquiry, "form": form},
    )


@staff_member_required(login_url="/dashboard/login/")
@require_POST
@transaction.atomic
def convert_custom_order(request, inquiry_id: int):
    inquiry = get_object_or_404(CustomOrderInquiry.objects.select_for_update(), pk=inquiry_id)
    try:
        order = create_order_for_custom_inquiry(request, inquiry)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return redirect("custom_order_detail", inquiry_id=inquiry.pk)
    messages.success(
        request,
        f"Oscar order {order.number} created. It is awaiting the Stripe invoice/payment phase.",
    )
    return redirect("custom_order_detail", inquiry_id=inquiry.pk)


@staff_member_required(login_url="/dashboard/login/")
@require_http_methods(["GET", "POST"])
def record_manual_sale(request):
    form = ManualSaleForm(request.POST or None)
    line_formset = ManualSaleLineFormSet(request.POST or None, prefix="sale-lines")
    if request.method == "POST" and form.is_valid() and line_formset.is_valid():
        line_items = [
            (line_form.cleaned_data["product"], line_form.cleaned_data["quantity"])
            for line_form in line_formset
            if line_form.cleaned_data.get("product")
        ]
        if not line_items:
            form.add_error(None, "Add at least one item to the sale.")
        else:
            payment_method = form.cleaned_data["payment_method"]
            payment_label = dict(ManualSaleForm.PaymentMethod.choices)[payment_method]
            try:
                order = create_oscar_order(
                    request,
                    line_items,
                    customer_email=form.cleaned_data["customer_email"],
                    note=(
                        "In-person sale. "
                        f"Payment method: {payment_label}. "
                        f"{form.cleaned_data['notes']}"
                    ).strip(),
                    payment_method=payment_label,
                    collect_in_person=True,
                )
            except InventoryUnavailable as exc:
                form.add_error(None, str(exc))
            except ValidationError as exc:
                form.add_error(None, "; ".join(exc.messages))
            else:
                messages.success(request, f"In-person sale recorded as Oscar order {order.number}.")
                return redirect("record_manual_sale")

    return render(
        request,
        "home/dashboard/record_manual_sale.html",
        {"form": form, "line_formset": line_formset},
    )
