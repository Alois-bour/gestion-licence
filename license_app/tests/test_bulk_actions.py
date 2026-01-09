from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from license_app.models import License, Customer, Product, ClientType
from license_app.admin import LicenseAdmin, bulk_update_dates, send_bulk_email
from license_app.forms import BulkUpdateDatesForm, BulkEmailForm

class MockSuperUser:
    def has_perm(self, perm):
        return True

class BulkActionTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.client_type = ClientType.objects.create(name="Bulk Test Type")
        self.customer = Customer.objects.create(name="Bulk Corp", email="bulk@example.com", client_type=self.client_type)
        self.product = Product.objects.create(name="Bulk Product")

        self.today = timezone.now().date()
        self.license = License.objects.create(
            license_number="LIC-BULK-1",
            customer=self.customer,
            product=self.product,
            status='active',
            expiry_date=self.today
        )
        self.license2 = License.objects.create(
            license_number="LIC-BULK-2",
            customer=self.customer,
            product=self.product,
            status='expired',
            expiry_date=self.today - timedelta(days=10)
        )
        self.queryset = License.objects.filter(id__in=[self.license.id, self.license2.id])
        self.admin = LicenseAdmin(License, self.site)

    def test_renew_year_action(self):
        """Test the bulk renewal logic (+365 days)."""
        # Mock request with 'apply' and form data
        request = self.factory.post('/', {
            'apply': '1',
            'action': 'renew_year',
        })
        # Proper message storage setup for tests
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request.user = MockSuperUser()

        # Call the action function directly
        bulk_update_dates(self.admin, request, self.queryset)

        self.license.refresh_from_db()
        self.license2.refresh_from_db()

        # License 1: Was today. Should be today + 365.
        expected_l1 = self.today + timedelta(days=365)
        self.assertEqual(self.license.expiry_date, expected_l1)

        # License 2: Was today-10. Should be today-10 + 365.
        expected_l2 = (self.today - timedelta(days=10)) + timedelta(days=365)
        self.assertEqual(self.license2.expiry_date, expected_l2)

        # Check status update
        self.assertEqual(self.license.status, 'active')

    def test_bulk_email_action(self):
        """Test sending bulk emails."""
        request = self.factory.post('/', {
            'apply': '1',
            'subject': 'Test Subject',
            'body': 'Hello {{ customer_name }}, your license {{ license_number }} expires on {{ expiry_date }}.',
        })
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request.user = MockSuperUser()

        send_bulk_email(self.admin, request, self.queryset)

        # Expect 2 emails (same customer, but loop sends per license)
        self.assertEqual(len(mail.outbox), 2)

        email1 = mail.outbox[0]
        self.assertIn("Hello Bulk Corp", email1.body)
        self.assertIn("LIC-BULK-1", email1.body)
        self.assertEqual(email1.to, ["bulk@example.com"])
