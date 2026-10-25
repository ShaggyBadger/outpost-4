from django.urls import path

from home.views import checkout_unavailable

app_name = "checkout"

urlpatterns = [
    path("", checkout_unavailable, name="index"),
    path("<path:step>/", checkout_unavailable, name="disabled_step"),
]
