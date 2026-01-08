from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

class Product(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du produit")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"


class License(models.Model):
    STATUS = [
        ("active", "Active"),
        ("expired", "Expirée"),
        ("suspended", "Suspendue"),
        ("pending", "En attente"),
    ]
    
    license_number = models.CharField(max_length=64, unique=True, verbose_name="Numéro de licence")
    customer = models.CharField(max_length=150, verbose_name="Client")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Date d'expiration")
    status = models.CharField(max_length=20, choices=STATUS, default='active', verbose_name="Statut")
    comment = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Licence"
        verbose_name_plural = "Licences"
        ordering = ['-expiry_date']

    def __str__(self):
        return f"{self.license_number} - {self.customer}"
    
    def clean(self):
        """Validation personnalisée"""
        if self.start_date and self.expiry_date:
            if self.start_date > self.expiry_date:
                raise ValidationError("La date de début ne peut pas être postérieure à la date d'expiration.")
        
        # Vérification si le produit existe avant de sauvegarder
        if self.product and not Product.objects.filter(id=self.product.id).exists():
            raise ValidationError(f"Le produit '{self.product}' n'existe pas.")

    def save(self, *args, **kwargs):
        """Auto-update du statut basé sur la date d'expiration"""
        if self.expiry_date and self.expiry_date < timezone.now().date():
            self.status = 'expired'
        super().save(*args, **kwargs)
    
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    is_expired.boolean = True
    is_expired.short_description = "Expirée ?"
    
    def days_until_expiry(self):
        """Calcule le nombre de jours avant expiration"""
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None
    
    def expiry_status(self):
        """Retourne un indicateur visuel du statut d'expiration"""
        days = self.days_until_expiry()
        if days is None:
            return "⚪ Non défini"
        elif days < 0:
            return "🔴 Expirée"
        elif days <= 30:
            return f"🟠 Expire dans {days} jours"
        elif days <= 90:
            return f"🟡 Expire dans {days} jours"
        else:
            return f"🟢 Expire dans {days} jours"
    
    expiry_status.short_description = "État d'expiration"
