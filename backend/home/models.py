from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Prefetch
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    """Starting page type for the public site."""

    intro = RichTextField(blank=True)
    hero_heading = models.CharField(
        max_length=120,
        default="Found quilts. Remade to be worn again.",
    )
    hero_copy = models.TextField(
        default=(
            "We find quilts at thrift shops and turn them into one-of-a-kind "
            "garments and accessories. Every piece carries its own past."
        )
    )
    story_heading = models.CharField(
        max_length=120,
        default="A new life for a well-loved textile.",
    )
    story_copy = models.TextField(
        default=(
            "GrannyCoded starts with quilts found in thrift shops and reimagines "
            "them as wearable pieces and useful keepsakes."
        )
    )

    content_panels = Page.content_panels + [
        FieldPanel("hero_heading"),
        FieldPanel("hero_copy"),
        FieldPanel("intro"),
        FieldPanel("story_heading"),
        FieldPanel("story_copy"),
    ]

    subpage_types = ["home.BlogIndexPage"]

    def get_context(self, request):
        context = super().get_context(request)
        from oscar.core.loading import get_model

        Product = get_model("catalogue", "Product")
        products = list(
            Product.objects.browsable()
            .exclude(structure=Product.CHILD)
            .select_related("product_class")
            .prefetch_related(
                "stockrecords",
                "images",
                Prefetch(
                    "children",
                    queryset=Product.objects.public().prefetch_related("stockrecords"),
                    to_attr="_prefetched_public_children",
                ),
            )
            .order_by("-priority", "-date_created")[:12]
        )

        def has_stock(product):
            if product.structure == Product.PARENT:
                stock_records = (
                    record
                    for child in product.get_public_children()
                    for record in child.stockrecords.all()
                )
            else:
                stock_records = iter(product.stockrecords.all())
            return any(
                (record.num_in_stock or 0) - (record.num_allocated or 0) > 0
                for record in stock_records
            )

        available_products = [product for product in products if has_stock(product)]
        context["featured_product"] = available_products[0] if available_products else None
        context["shop_preview"] = available_products[:3]
        context["recent_posts"] = (
            BlogPostPage.objects.live()
            .order_by("-first_published_at")
            .specific()[:3]
        )
        return context

    class Meta:
        verbose_name = "home page"


class BlogIndexPage(Page):
    """Index of maker journal posts."""

    intro = models.TextField(blank=True)

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.BlogPostPage"]
    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request):
        context = super().get_context(request)
        context["posts"] = (
            BlogPostPage.objects.child_of(self)
            .live()
            .order_by("-first_published_at")
            .specific()
        )
        return context


class CustomOrderInquiry(models.Model):
    """A customer request that the maker reviews before quoting custom work."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        REVIEWING = "reviewing", "Reviewing"
        QUOTED = "quoted", "Quoted"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        CONVERTED = "converted", "Converted to order"

    name = models.CharField(max_length=120)
    email = models.EmailField()
    request_details = models.TextField(max_length=5000)
    reference_photo = models.ImageField(
        upload_to="custom-order-inquiries/%Y/%m/",
        blank=True,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    quoted_total = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quoted_shipping = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    shipping_note = models.CharField(max_length=255, blank=True)
    maker_notes = models.TextField(blank=True)
    order = models.ForeignKey(
        "order.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="custom_order_inquiries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Custom inquiry from {self.name} ({self.get_status_display()})"


class BlogPostPage(Page):
    """An article in the GrannyCoded journal."""

    excerpt = models.CharField(max_length=280, blank=True)
    body = RichTextField(blank=True)
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    parent_page_types = ["home.BlogIndexPage"]
    subpage_types = []
    content_panels = Page.content_panels + [
        FieldPanel("excerpt"),
        FieldPanel("body"),
        FieldPanel("cover_image"),
    ]


@register_setting
class BrandSettings(BaseSiteSetting):
    """Site-wide social links and short maker introduction."""

    maker_note = models.TextField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    pinterest_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)

    panels = [
        FieldPanel("maker_note"),
        FieldPanel("instagram_url"),
        FieldPanel("facebook_url"),
        FieldPanel("pinterest_url"),
        FieldPanel("tiktok_url"),
    ]
