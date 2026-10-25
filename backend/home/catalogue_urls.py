from django.urls import path, re_path

from home.views import OscarCatalogueView, OscarCategoryView, ProductDetailView

app_name = "catalogue"

urlpatterns = [
    path("", OscarCatalogueView.as_view(), name="index"),
    re_path(
        r"^(?P<product_slug>[\w-]*)_(?P<pk>\d+)/$",
        ProductDetailView.as_view(),
        name="detail",
    ),
    re_path(
        r"^category/(?P<category_slug>[\w-]+(/[\w-]+)*)_(?P<pk>\d+)/$",
        OscarCategoryView.as_view(),
        name="category",
    ),
]
