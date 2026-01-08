from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
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

        alerts_sent = 0

        if expiring_licenses.exists():
            self.stdout.write(self.style.WARNING(f"⚠️ FOUND {expiring_licenses.count()} EXPIRING LICENSE(S):"))

            # Group by customer or send individually. Let's send individually for simplicity and direct alerting.
            for license in expiring_licenses:
                days_left = (license.expiry_date - today).days
                message = f" - [{license.license_number}] {license.customer} (Expires in {days_left} days on {license.expiry_date})"
                self.stdout.write(message)

                # Send email to Customer if email exists
                if license.customer.email:
                    subject = f"Avis d'expiration de licence: {license.product.name}"
                    body = (
                        f"Bonjour {license.customer.name},\n\n"
                        f"Votre licence pour le produit '{license.product.name}' (Numéro: {license.license_number}) "
                        f"expire dans {days_left} jours (le {license.expiry_date}).\n\n"
                        f"Merci de nous contacter pour le renouvellement.\n\n"
                        f"Cordialement,\nL'équipe License Manager"
                    )
                    try:
                        send_mail(
                            subject,
                            body,
                            settings.DEFAULT_FROM_EMAIL,
                            [license.customer.email],
                            fail_silently=False,
                        )
                        self.stdout.write(self.style.SUCCESS(f"   -> Email sent to {license.customer.email}"))
                        alerts_sent += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"   -> Failed to send email to {license.customer.email}: {e}"))

            # Send summary to Admin
            admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
            # If ADMINS not configured, assume a default for the sake of the exercise or just skip
            if not admin_emails:
                admin_emails = ['admin@licensemanager.local'] # Fallback

            summary_subject = f"[License Manager] {expiring_licenses.count()} licences expirent bientôt"
            summary_body = "Les licences suivantes expirent dans les 30 jours :\n\n"
            for license in expiring_licenses:
                summary_body += f"- {license.customer.name} / {license.product.name} ({license.license_number}) : Expire le {license.expiry_date}\n"

            send_mail(
                summary_subject,
                summary_body,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True
            )
            self.stdout.write(self.style.SUCCESS(f"-> Summary email sent to admins: {', '.join(admin_emails)}"))

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
