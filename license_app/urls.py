from django.urls import path
from .views import import_with_mapping

app_name = 'license_app'

urlpatterns = [
    path('import-mapping/', import_with_mapping, name='import_mapping'),
]
