from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from license_app.models import Customer, License, Product, ClientType
from django.utils import timezone
from datetime import timedelta
from io import StringIO

class FeatureTests(TestCase):
    def setUp(self):
        self.client_type = ClientType.objects.create(name="Feature Test Type")
        self.customer = Customer.objects.create(name="Feature Corp", email="feature@example.com", client_type=self.client_type)
        self.product = Product.objects.create(name="Feature Product")

    def test_history_creation(self):
        """Test that history is tracked when a model is modified."""
        license = License.objects.create(
            license_number="LIC-HIST-1",
            customer=self.customer,
            product=self.product,
            status='active'
        )
        self.assertEqual(license.history.count(), 1)

        license.status = 'suspended'
        license.save()
        self.assertEqual(license.history.count(), 2)

        self.assertEqual(license.history.first().status, 'suspended')
        self.assertEqual(license.history.last().status, 'active')

    def test_email_alert_sending(self):
        """Test that check_expirations sends emails."""
        today = timezone.now().date()
        License.objects.create(
            license_number="LIC-EMAIL-TEST",
            customer=self.customer,
            product=self.product,
            expiry_date=today + timedelta(days=5),
            status='active'
        )

        out = StringIO()
        call_command('check_expirations', stdout=out)

        # Check that emails were sent
        # We expect 2 emails: 1 to customer, 1 to admin
        self.assertEqual(len(mail.outbox), 2)

        # Check customer email
        customer_email = mail.outbox[0]
        self.assertIn("Avis d'expiration", customer_email.subject)
        self.assertIn("Feature Corp", customer_email.body)
        self.assertEqual(customer_email.to, ["feature@example.com"])

        # Check admin email
        admin_email = mail.outbox[1]
        self.assertIn("licences expirent bientôt", admin_email.subject)
