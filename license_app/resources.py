# license_app/resources.py

from import_export import resources
from .models import License

class LicenseResource(resources.ModelResource):
    class Meta:
        model = License
        fields = ('id', 'license_number', 'customer', 'product', 'start_date', 'expiry_date', 'status', 'comment', 'created_at', 'updated_at')
        export_order = ('license_number', 'customer', 'product', 'start_date', 'expiry_date', 'status', 'comment', 'created_at', 'updated_at')
