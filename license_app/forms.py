from django import forms
from django.utils import timezone
from .models import Product, License

class SetProductForm(forms.Form):
    new_product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Nouveau produit",
        empty_label="--- Sélectionner un produit ---",
        required=True,
    )


class BulkStatusForm(forms.Form):
    new_status = forms.ChoiceField(
        choices=License.STATUS,
        label="Nouveau statut",
        required=True,
    )
    comment = forms.CharField(
        label="Commentaire (optionnel)",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
    )


class BulkUpdateDatesForm(forms.Form):

    ACTION_EXTEND = 'extend'
    ACTION_SET_START = 'set_start'
    ACTION_SET_EXPIRY = 'set_expiry'

    ACTION_CHOICES = (
        (ACTION_EXTEND, "➕ Prolonger la date d'expiration"),
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
