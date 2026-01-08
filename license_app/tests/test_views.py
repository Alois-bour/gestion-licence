from django.test import TestCase, Client
from django.contrib.auth.models import User
from license_app.models import Customer, License, Product
from django.utils import timezone
from datetime import timedelta

class FrontOfficeTests(TestCase):
    def setUp(self):
        # Setup User
        self.user = User.objects.create_user(username='testuser', password='password')
        self.other_user = User.objects.create_user(username='otheruser', password='password')

        # Setup Data
        self.product = Product.objects.create(name="Test Product")
        self.customer = Customer.objects.create(name="Test Corp")
        self.customer.users.add(self.user)

        self.other_customer = Customer.objects.create(name="Other Corp")
        self.other_customer.users.add(self.other_user)

        # License for User
        self.license1 = License.objects.create(
            license_number="LIC-USER-1",
            customer=self.customer,
            product=self.product,
            status='active'
        )

        # License for Other User
        self.license2 = License.objects.create(
            license_number="LIC-OTHER-1",
            customer=self.other_customer,
            product=self.product,
            status='active'
        )

        self.client = Client()

    def test_login_required(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_dashboard_shows_user_licenses(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LIC-USER-1")
        self.assertNotContains(response, "LIC-OTHER-1")

    def test_dashboard_shows_no_licenses_for_other_user(self):
        self.client.login(username='otheruser', password='password')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LIC-OTHER-1")
        self.assertNotContains(response, "LIC-USER-1")
