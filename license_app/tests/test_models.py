from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from license_app.models import License, Customer, ClientType, Product
from django.db.utils import IntegrityError

class LicenseTests(TestCase):
    def setUp(self):
        self.client_type = ClientType.objects.create(name="Standard")
        self.customer = Customer.objects.create(name="Test Corp", client_type=self.client_type)
        self.product = Product.objects.create(name="Test Product")

    def test_duplicate_license_number(self):
        """Test that duplicate license numbers are not allowed."""
        License.objects.create(
            license_number="LIC-DUP",
            customer=self.customer,
            product=self.product
        )
        with self.assertRaises(IntegrityError):
            License.objects.create(
                license_number="LIC-DUP",
                customer=self.customer,
                product=self.product
            )

    def test_expiring_licenses(self):
        """Test the logic for identifying expiring licenses."""
        today = timezone.now().date()

        # Expiring in 10 days
        l1 = License.objects.create(
            license_number="LIC-EXP-1",
            customer=self.customer,
            product=self.product,
            expiry_date=today + timedelta(days=10),
            status='active'
        )

        # Expiring in 60 days
        l2 = License.objects.create(
            license_number="LIC-OK-1",
            customer=self.customer,
            product=self.product,
            expiry_date=today + timedelta(days=60),
            status='active'
        )

        # Expired
        l3 = License.objects.create(
            license_number="LIC-OLD-1",
            customer=self.customer,
            product=self.product,
            expiry_date=today - timedelta(days=1),
            status='active' # Should be marked expired by check, but let's test logic
        )

        # Check logic similar to command
        expiring_threshold = today + timedelta(days=30)
        expiring = License.objects.filter(
            status='active',
            expiry_date__lte=expiring_threshold,
            expiry_date__gte=today
        )

        self.assertIn(l1, expiring)
        self.assertNotIn(l2, expiring)
        self.assertNotIn(l3, expiring)
