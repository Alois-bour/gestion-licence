from django.core.management.base import BaseCommand
from django.utils import timezone
from license_app.models import License
from datetime import timedelta

class Command(BaseCommand):
    help = 'Checks for expiring licenses and sends alerts'

    def handle(self, *args, **options):
        today = timezone.now().date()
        expiring_threshold = today + timedelta(days=30)

        # Check for expiring licenses (active and expiry_date within 30 days)
        expiring_licenses = License.objects.filter(
            status='active',
            expiry_date__lte=expiring_threshold,
            expiry_date__gte=today
        )

        self.stdout.write(self.style.NOTICE(f"Checking for expiring licenses..."))

        if expiring_licenses.exists():
            self.stdout.write(self.style.WARNING(f"⚠️ FOUND {expiring_licenses.count()} EXPIRING LICENSE(S):"))
            for license in expiring_licenses:
                days_left = (license.expiry_date - today).days
                self.stdout.write(f" - [{license.license_number}] {license.customer} (Expires in {days_left} days on {license.expiry_date})")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No licenses expiring within the next 30 days."))

        # Check for already expired active licenses
        expired_licenses = License.objects.filter(
            status='active',
            expiry_date__lt=today
        )

        if expired_licenses.exists():
            self.stdout.write(self.style.ERROR(f"\n🔴 FOUND {expired_licenses.count()} EXPIRED BUT ACTIVE LICENSE(S):"))
            for license in expired_licenses:
                self.stdout.write(f" - [{license.license_number}] {license.customer} (Expired on {license.expiry_date})")
