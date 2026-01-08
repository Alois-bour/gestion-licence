from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("license-app/", include("license_app.urls", namespace="license_app")),
]
