from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import timedelta
from simple_history.models import HistoricalRecords

class ClientType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Type de client")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Type de client"
        verbose_name_plural = "Types de clients"


class Customer(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Nom")
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    client_type = models.ForeignKey(ClientType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de client")
    users = models.ManyToManyField(User, related_name='customers', blank=True, verbose_name="Utilisateurs associés")
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"


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
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Client")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Date d'expiration")
    status = models.CharField(max_length=20, choices=STATUS, default='active', verbose_name="Statut")
    comment = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    history = HistoricalRecords()

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

    def _update_status_from_expiry(self):
        """Met à jour le statut si la date d'expiration est passée"""
        if self.expiry_date and self.expiry_date < timezone.now().date():
            self.status = 'expired'

    def extend_validity(self, days, save=True):
        """Prolonge la validité de la licence"""
        if self.expiry_date:
            self.expiry_date += timedelta(days=days)
            self._update_status_from_expiry()
            if save:
                self.save()

    def change_product(self, product, save=True):
        """Change le produit de la licence"""
        self.product = product
        if save:
            self.save()

    def change_status(self, status, comment=None, save=True):
        """Change le statut de la licence et ajoute un commentaire"""
        self.status = status
        if comment:
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            self.comment = (self.comment or '') + f"\n[{timestamp}] {comment}"
        if save:
            self.save()

    def activate(self, save=True):
        """Active la licence"""
        self.change_status('active', save=save)

    def suspend(self, save=True):
        """Suspend la licence"""
        self.change_status('suspended', save=save)

    def save(self, *args, **kwargs):
        """Auto-update du statut basé sur la date d'expiration"""
        self._update_status_from_expiry()
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
