from decimal import Decimal
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from wagtail.models import Site

from home.models import BlogIndexPage, BlogPostPage, CustomOrderInquiry, HomePage
from oscar.core.loading import get_model


class StorefrontTests(TestCase):
    def setUp(self):
        self.home = Site.objects.get(is_default_site=True).root_page.specific
        self.product_class = get_model("catalogue", "ProductClass").objects.get(
            slug="handmade-goods"
        )
        self.partner = get_model("partner", "Partner").objects.get(
            code="grannycoded"
        )
        self.category = get_model("catalogue", "Category").objects.get(
            slug="wearables"
        )
        self.Product = get_model("catalogue", "Product")
        self.StockRecord = get_model("partner", "StockRecord")
        self.ProductAttribute = get_model("catalogue", "ProductAttribute")
        self.ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")

    def create_product(
        self,
        *,
        slug="mimi-quilt-coat",
        title="Mimi Quilt Coat",
        price=Decimal("179.00"),
        stock=1,
        is_public=True,
        one_of_a_kind=True,
    ):
        product = self.Product.objects.create(
            title=title,
            slug=slug,
            description="A handmade piece created from a found quilt.",
            product_class=self.product_class,
            is_public=is_public,
        )
        product.categories.add(self.category)
        self.StockRecord.objects.create(
            product=product,
            partner=self.partner,
            partner_sku=slug,
            price_currency="USD",
            price=price,
            num_in_stock=stock,
            num_allocated=0,
        )
        one_of_a_kind_attribute = self.ProductAttribute.objects.get(
            product_class=self.product_class,
            code="one_of_a_kind",
        )
        self.ProductAttributeValue.objects.create(
            product=product,
            attribute=one_of_a_kind_attribute,
            value_boolean=one_of_a_kind,
        )
        image_path_attribute = self.ProductAttribute.objects.get(
            product_class=self.product_class,
            code="static_image_path",
        )
        self.ProductAttributeValue.objects.create(
            product=product,
            attribute=image_path_attribute,
            value_text="images/products/the-mimi-coat-blue-ribbon-winning-quilt.webp",
        )
        image_alt_attribute = self.ProductAttribute.objects.get(
            product_class=self.product_class,
            code="image_alt",
        )
        self.ProductAttributeValue.objects.create(
            product=product,
            attribute=image_alt_attribute,
            value_text="A handmade quilt coat",
        )
        return product

    def test_default_site_root_is_the_editable_home_page(self):
        self.assertIsInstance(self.home, HomePage)

    def test_home_page_renders_brand_story_and_oscar_catalogue_preview(self):
        self.create_product()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Found quilts. Remade to be worn again.")
        self.assertContains(response, 'href="/shop/"')
        self.assertContains(response, "Mimi Quilt Coat")

    def test_oscar_catalogue_and_product_detail_use_the_brand_templates(self):
        product = self.create_product()

        shop_response = self.client.get(reverse("catalogue:index"))
        self.assertEqual(shop_response.status_code, 200)
        self.assertContains(shop_response, product.title)
        self.assertContains(shop_response, "$179.00")
        self.assertContains(shop_response, "One of a kind · available")

        detail_response = self.client.get(product.get_absolute_url())
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, product.title)
        self.assertContains(detail_response, "Add to bag")

    def test_category_and_search_browse_filter_oscar_products(self):
        product = self.create_product()

        category_response = self.client.get(self.category.get_absolute_url())
        search_response = self.client.get(reverse("catalogue:index"), {"q": "Mimi"})

        self.assertContains(category_response, product.title)
        self.assertContains(search_response, product.title)

    def test_sold_one_off_remains_visible_but_cannot_be_added_to_basket(self):
        product = self.create_product(stock=0)

        shop_response = self.client.get(reverse("catalogue:index"))
        detail_response = self.client.get(product.get_absolute_url())

        self.assertContains(shop_response, "Sold")
        self.assertContains(detail_response, "This piece has sold.")
        self.assertNotContains(detail_response, "Add to bag")
        self.assertContains(detail_response, "Ask about custom work")

    def test_product_description_is_html_escaped(self):
        product = self.create_product()
        product.description = '<script>alert("x")</script>'
        product.save()

        response = self.client.get(product.get_absolute_url())

        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>")

    def test_variant_stock_and_price_are_managed_on_each_child_product(self):
        parent = self.Product.objects.create(
            title="Quilted Market Bag",
            slug="quilted-market-bag",
            structure=self.Product.PARENT,
            product_class=self.product_class,
            is_public=True,
        )
        parent.categories.add(self.category)
        variant = self.Product.objects.create(
            title="Large",
            slug="quilted-market-bag-large",
            structure=self.Product.CHILD,
            parent=parent,
            is_public=True,
        )
        self.StockRecord.objects.create(
            product=variant,
            partner=self.partner,
            partner_sku="quilted-market-bag-large",
            price_currency="USD",
            price=Decimal("55.00"),
            num_in_stock=3,
            num_allocated=0,
        )

        parent_response = self.client.get(parent.get_absolute_url())
        variant_response = self.client.get(variant.get_absolute_url())

        self.assertContains(parent_response, "Choose a version")
        self.assertContains(parent_response, variant.get_absolute_url())
        self.assertContains(variant_response, "Large")
        self.assertContains(variant_response, "$55.00")
        self.assertContains(variant_response, "Add to bag")

        self.client.post(
            reverse("basket:add", kwargs={"pk": variant.pk}),
            {"quantity": 1, "next": variant.get_absolute_url()},
            HTTP_REFERER=variant.get_absolute_url(),
        )
        basket = self.client.get(reverse("basket:summary")).wsgi_request.basket
        self.assertEqual(basket.lines.get().product, variant)

    def test_basket_uses_oscar_lines_and_checkout_is_disabled(self):
        product = self.create_product()
        add_response = self.client.post(
            reverse("basket:add", kwargs={"pk": product.pk}),
            {"quantity": 1, "next": product.get_absolute_url()},
            HTTP_REFERER=product.get_absolute_url(),
        )

        self.assertEqual(add_response.status_code, 302)
        basket_response = self.client.get(reverse("basket:summary"))
        self.assertEqual(basket_response.status_code, 200)
        self.assertContains(basket_response, product.title)
        self.assertContains(basket_response, "Checkout opening soon")

        checkout_response = self.client.get(reverse("checkout:index"))
        self.assertEqual(checkout_response.status_code, 200)
        self.assertContains(checkout_response, "Online checkout is opening soon.")

    def test_journal_pages_render_editorial_content(self):
        self.assertNotContains(self.client.get("/"), 'href="/journal/"')
        journal = self.home.add_child(
            instance=BlogIndexPage(
                title="Journal",
                slug="journal",
                intro="Notes from the studio.",
            )
        )
        journal.save_revision().publish()
        post = journal.add_child(
            instance=BlogPostPage(
                title="A Quilt Finds a New Life",
                slug="quilt-new-life",
                excerpt="A short note about remaking textiles.",
            )
        )
        post.save_revision().publish()

        journal_response = self.client.get("/journal/")
        post_response = self.client.get("/journal/quilt-new-life/")

        self.assertEqual(journal_response.status_code, 200)
        self.assertContains(journal_response, post.title)
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, post.excerpt)
        self.assertContains(self.client.get("/"), 'href="/journal/"')

    def test_custom_order_request_is_saved_for_wagtail_review(self):
        response = self.client.post(
            reverse("custom_order_request"),
            {
                "name": "Taylor Shopper",
                "email": "taylor@example.com",
                "request_details": "I would love a quilt coat with deep pockets.",
            },
        )

        self.assertEqual(response.status_code, 302)
        inquiry = CustomOrderInquiry.objects.get()
        self.assertEqual(inquiry.name, "Taylor Shopper")
        self.assertEqual(inquiry.status, CustomOrderInquiry.Status.NEW)
        self.assertContains(self.client.get(reverse("custom_order_request")), "Custom work")

    def test_custom_order_request_accepts_an_optional_reference_photo(self):
        image_bytes = BytesIO()
        Image.new("RGB", (2, 2), color="olive").save(image_bytes, format="JPEG")
        photo = SimpleUploadedFile(
            "reference.jpg",
            image_bytes.getvalue(),
            content_type="image/jpeg",
        )
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            response = self.client.post(
                reverse("custom_order_request"),
                {
                    "name": "Taylor Shopper",
                    "email": "taylor@example.com",
                    "request_details": "A coat inspired by this reference.",
                    "reference_photo": photo,
                },
            )
            inquiry = CustomOrderInquiry.objects.get()
            self.assertTrue(inquiry.reference_photo.name.endswith(".jpg"))

        self.assertEqual(response.status_code, 302)

    def test_accepted_custom_quote_creates_a_private_pending_oscar_order(self):
        inquiry = CustomOrderInquiry.objects.create(
            name="Taylor Shopper",
            email="taylor@example.com",
            request_details="A custom quilt coat with deep pockets.",
            status=CustomOrderInquiry.Status.NEW,
        )
        staff = get_user_model().objects.create_superuser(
            username="leah",
            email="leah@example.com",
            password="test-password",
        )
        self.client.force_login(staff)

        quote_response = self.client.post(
            reverse("custom_order_detail", kwargs={"inquiry_id": inquiry.pk}),
            {
                "status": CustomOrderInquiry.Status.ACCEPTED,
                "quoted_total": "150.00",
                "quoted_shipping": "10.00",
                "shipping_note": "U.S. shipping included in the agreed total.",
                "maker_notes": "Use the floral quilt Leah selected.",
            },
        )
        self.assertEqual(quote_response.status_code, 302)

        convert_response = self.client.post(
            reverse("convert_custom_order", kwargs={"inquiry_id": inquiry.pk})
        )

        self.assertEqual(convert_response.status_code, 302)
        inquiry.refresh_from_db()
        order = get_model("order", "Order").objects.get()
        line = order.lines.get()
        stockrecord = self.StockRecord.objects.get(pk=line.stockrecord_id)
        self.assertEqual(inquiry.status, CustomOrderInquiry.Status.CONVERTED)
        self.assertEqual(inquiry.order, order)
        self.assertEqual(order.status, "Pending")
        self.assertEqual(order.guest_email, "taylor@example.com")
        self.assertEqual(order.total_incl_tax, Decimal("150.00"))
        self.assertEqual(stockrecord.num_allocated, 1)
        self.assertFalse(order.lines.get().product.is_public)

    def test_in_person_custom_order_can_be_recorded_after_quote_acceptance(self):
        staff = get_user_model().objects.create_superuser(
            username="custom-maker",
            email="leah@example.com",
            password="test-password",
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse("create_in_person_custom_order"),
            {
                "name": "Jordan Shopper",
                "email": "jordan@example.com",
                "request_details": "A quilt coat with two deep pockets.",
                "quoted_total": "150.00",
                "quoted_shipping": "0.00",
                "shipping_note": "Pickup at the craft fair.",
                "maker_notes": "Customer accepted the quote in person.",
            },
        )

        self.assertEqual(response.status_code, 302)
        inquiry = CustomOrderInquiry.objects.get()
        order = inquiry.order
        self.assertEqual(inquiry.status, CustomOrderInquiry.Status.CONVERTED)
        self.assertIsNotNone(order)
        self.assertEqual(order.status, "Pending")
        self.assertEqual(order.guest_email, "jordan@example.com")
        self.assertEqual(order.total_incl_tax, Decimal("150.00"))

    def test_in_person_sale_records_paid_order_and_consumes_unpublished_stock(self):
        product = self.create_product(stock=1, is_public=False)
        staff = get_user_model().objects.create_superuser(
            username="market-maker",
            email="leah@example.com",
            password="test-password",
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse("record_manual_sale"),
            {
                "payment_method": "cash",
                "customer_email": "",
                "notes": "Saturday craft fair",
                "sale-lines-TOTAL_FORMS": "1",
                "sale-lines-INITIAL_FORMS": "0",
                "sale-lines-MIN_NUM_FORMS": "1",
                "sale-lines-MAX_NUM_FORMS": "10",
                "sale-lines-0-product": str(product.pk),
                "sale-lines-0-quantity": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        order = get_model("order", "Order").objects.get()
        line = order.lines.get()
        stockrecord = self.StockRecord.objects.get(product=product)
        self.assertEqual(order.status, "Complete")
        self.assertEqual(order.guest_email, "")
        self.assertEqual(order.payment_events.get().event_type.code, "paid")
        self.assertEqual(order.shipping_events.get().event_type.code, "collected")
        self.assertEqual(stockrecord.num_in_stock, 0)
        self.assertEqual(stockrecord.num_allocated, 0)
        self.assertEqual(line.status, "Complete")

    def test_oscar_shop_tools_require_a_staff_user(self):
        response = self.client.get(reverse("record_manual_sale"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/login/", response.url)

    def test_oscar_dashboard_exposes_grannycoded_shop_tools_to_staff(self):
        staff = get_user_model().objects.create_superuser(
            username="shop-manager",
            email="manager@example.com",
            password="test-password",
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Custom orders")
        self.assertContains(response, "Record in-person sale")

        catalogue_response = self.client.get(reverse("dashboard:catalogue-product-list"))
        self.assertEqual(catalogue_response.status_code, 200)
        self.assertContains(catalogue_response, "Products")

    def test_catalog_import_creates_private_zero_stock_oscar_drafts_idempotently(self):
        call_command("import_granny_catalog")
        call_command("import_granny_catalog")

        product = self.Product.objects.get(slug="floral-duster-coat-vintage-tablecloth")
        stockrecord = self.StockRecord.objects.get(product=product)
        self.assertEqual(self.Product.objects.count(), 12)
        self.assertFalse(product.is_public)
        self.assertEqual(product.priority, 1)
        self.assertEqual(stockrecord.num_in_stock, 0)
        self.assertEqual(stockrecord.price, Decimal("95.00"))
        self.assertEqual(
            product.attr.static_image_path,
            "images/products/floral-duster-coat-vintage-tablecloth.webp",
        )
