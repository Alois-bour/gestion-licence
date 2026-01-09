from django import forms
from django.utils import timezone
from .models import Product

class SetProductForm(forms.Form):
    new_product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Nouveau produit",
        empty_label="--- Sélectionner un produit ---",
        required=True,
    )


class BulkUpdateDatesForm(forms.Form):

    ACTION_EXTEND = 'extend'
    ACTION_RENEW_YEAR = 'renew_year'
    ACTION_SET_START = 'set_start'
    ACTION_SET_EXPIRY = 'set_expiry'

    ACTION_CHOICES = (
        (ACTION_EXTEND, "➕ Prolonger la date d'expiration (jours)"),
        (ACTION_RENEW_YEAR, "🔄 Renouveler pour 1 an (+365 jours)"),
        (ACTION_SET_START, "📅 Définir la date de début"),
        (ACTION_SET_EXPIRY, "⏰ Définir la date d'expiration"),
    )

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label="Action à effectuer",
        widget=forms.RadioSelect,
        required=True,
    )

    extension_days = forms.IntegerField(
        label="Nombre de jours à ajouter",
        min_value=1,
        required=False,
        help_text="Utilisé uniquement pour la prolongation.",
    )

    start_date = forms.DateField(
        label="Nouvelle date de début",
        required=False,
        widget=forms.SelectDateWidget(
            years=range(timezone.now().year - 5, timezone.now().year + 10)
        ),
    )

    expiry_date = forms.DateField(
        label="Nouvelle date d'expiration",
        required=False,
        widget=forms.SelectDateWidget(
            years=range(timezone.now().year - 5, timezone.now().year + 10)
        ),
    )

    def clean(self):
        cleaned = super().clean()
        action = cleaned.get('action')

        if action == self.ACTION_EXTEND and not cleaned.get('extension_days'):
            self.add_error('extension_days', "Ce champ est obligatoire.")

        if action == self.ACTION_SET_START and not cleaned.get('start_date'):
            self.add_error('start_date', "Ce champ est obligatoire.")

        if action == self.ACTION_SET_EXPIRY and not cleaned.get('expiry_date'):
            self.add_error('expiry_date', "Ce champ est obligatoire.")

        return cleaned


class BulkStatusForm(forms.Form):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expirée"),
        ("suspended", "Suspendue"),
        ("pending", "En attente"),
    ]

    new_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Nouveau statut",
        required=True
    )

    comment = forms.CharField(
        label="Commentaire (optionnel)",
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )


class BulkEmailForm(forms.Form):
    subject = forms.CharField(
        label="Sujet",
        max_length=200,
        required=True
    )

    body = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={'rows': 10}),
        required=True,
        help_text="Variables: {{ license_number }}, {{ product }}, {{ expiry_date }}, {{ customer_name }}"
    )
