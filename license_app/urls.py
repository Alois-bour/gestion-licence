from django.urls import path

from .views import import_with_mapping, reporting_dashboard

app_name = "license_app"

urlpatterns = [
    path("import-mapping/", import_with_mapping, name="import_mapping"),
    path("reporting/", reporting_dashboard, name="reporting_dashboard"),
]
