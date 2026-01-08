from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Editeur(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Éditeur")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Éditeur"
        verbose_name_plural = "Éditeurs"


class Entite(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Entité")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Entité"
        verbose_name_plural = "Entités"


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Service")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"


class CategorieUtilisateur(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name="Catégorie utilisateur"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Catégorie utilisateur"
        verbose_name_plural = "Catégories utilisateur"


class ClientType(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name="Nom du type de client"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Type de client"
        verbose_name_plural = "Types de client"


class Customer(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nom du client")
    client_type = models.ForeignKey(
        ClientType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Type de client",
    )
    nom_prenom_contact = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Nom et prénom du contact"
    )
    email_contact = models.EmailField(
        blank=True, null=True, verbose_name="Email du contact"
    )
    numero_telephone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Numéro de téléphone"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"


class Product(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du produit")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    editeur = models.ForeignKey(
        Editeur, on_delete=models.CASCADE, verbose_name="Éditeur"
    )

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

    # Core License Info
    license_number = models.CharField(
        max_length=100, unique=True, verbose_name="Numéro de licence / dongle"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Produit"
    )

    # Users & Contacts
    donneur_d_ordre = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Donneur d’ordre"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, verbose_name="End user réel"
    )
    end_user_declare = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="End user déclaré"
    )
    contact_de_livraison = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Contact de livraison"
    )

    # License Details
    type_de_licence = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Type de licence"
    )
    numero_licence_optionnel = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Numéro de licence optionnel (GK, RECON, Sale ID…)",
    )
    pack = models.CharField(max_length=100, blank=True, null=True, verbose_name="Pack")
    identifiant_pack = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Identifiant pack"
    )

    # Dates
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    expiry_date = models.DateField(verbose_name="Date d’échéance")
    date_de_livraison = models.DateField(
        null=True, blank=True, verbose_name="Date de livraison"
    )

    # Organizational Info
    categorie_utilisateur = models.ForeignKey(
        CategorieUtilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Catégorie utilisateur",
    )
    entite = models.ForeignKey(
        Entite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Entité"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Service",
    )
    numero_rio = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Numéro RIO"
    )

    # Order Info
    marche_hors_marche = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Marché / Hors marché"
    )
    numero_ej_bdc = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Numéro EJ / BDC"
    )
    derniere_commande = models.CharField(
        max_length=100, verbose_name="Dernière commande"
    )
    date_derniere_commande = models.DateField(verbose_name="Date de dernière commande")
    numero_commande_sap = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Numéro de commande SAP"
    )
    support = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Support (ex : R226)"
    )

    # Status & Metadata
    status = models.CharField(
        max_length=20, choices=STATUS, default="active", verbose_name="Statut"
    )
    remarques = models.TextField(blank=True, null=True, verbose_name="Remarques")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    class Meta:
        verbose_name = "Licence"
        verbose_name_plural = "Licences"
        ordering = ["-expiry_date"]

    def __str__(self):
        return f"{self.license_number} - {self.customer}"

    def clean(self):
        # Ensures that the start date is not after the expiry date.
        if self.start_date and self.expiry_date and self.start_date > self.expiry_date:
            raise ValidationError(
                "La date d'échéance ne peut pas être antérieure à la date de début."
            )

    def save(self, *args, **kwargs):
        if self.expiry_date and self.expiry_date < timezone.now().date():
            self.status = "expired"
        super().save(*args, **kwargs)

    def days_until_expiry(self):
        if self.expiry_date:
            return (self.expiry_date - timezone.now().date()).days
        return None

    def is_expiring_soon(self, days=30):
        d = self.days_until_expiry()
        return d is not None and 0 <= d <= days

    is_expiring_soon.boolean = True
    is_expiring_soon.short_description = "Expire bientôt ?"
