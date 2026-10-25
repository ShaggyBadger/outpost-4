from django.db import migrations


def clear_unverified_stock(apps, schema_editor):
    database = schema_editor.connection.alias
    Product = apps.get_model("catalogue", "Product")
    ProductAttribute = apps.get_model("catalogue", "ProductAttribute")
    ProductAttributeValue = apps.get_model("catalogue", "ProductAttributeValue")
    StockRecord = apps.get_model("partner", "StockRecord")

    source_attribute = ProductAttribute.objects.using(database).filter(
        product_class__slug="handmade-goods",
        code="source_listing_url",
    ).first()
    if source_attribute is None:
        return

    draft_product_ids = ProductAttributeValue.objects.using(database).filter(
        attribute=source_attribute,
        value_text__gt="",
        product__is_public=False,
    ).values_list("product_id", flat=True)
    StockRecord.objects.using(database).filter(product_id__in=draft_product_ids).update(
        num_in_stock=0,
        num_allocated=0,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0005_customorderinquiry_and_more"),
        ("catalogue", "0032_category_exclude_from_menu_category_long_description"),
        ("partner", "0007_partneraddress_code"),
    ]

    operations = [migrations.RunPython(clear_unverified_stock)]
