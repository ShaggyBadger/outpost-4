from django.db import migrations


def seed_order_events(apps, schema_editor):
    database = schema_editor.connection.alias
    PaymentEventType = apps.get_model("order", "PaymentEventType")
    ShippingEventType = apps.get_model("order", "ShippingEventType")

    for code, name in (
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ):
        PaymentEventType.objects.using(database).get_or_create(
            code=code,
            defaults={"name": name},
        )

    for code, name in (
        ("shipped", "Shipped"),
        ("collected", "Collected in person"),
        ("returned", "Returned"),
        ("cancelled", "Cancelled"),
    ):
        ShippingEventType.objects.using(database).get_or_create(
            code=code,
            defaults={"name": name},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0006_clear_unverified_draft_stock"),
        ("order", "0021_billingaddress_code_shippingaddress_code"),
    ]

    operations = [migrations.RunPython(seed_order_events, migrations.RunPython.noop)]
