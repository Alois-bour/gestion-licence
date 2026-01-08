from django import forms

from .models import License, Product


class SetProductForm(forms.Form):
    new_product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Nouveau produit",
        required=True,
    )


class BulkUpdateDatesForm(forms.Form):
    ACTION_CHOICES = (
        ("extend", "Prolonger la date d'expiration"),
        ("set_start", "Définir la date de début"),
        ("set_expiry", "Définir la date d'expiration"),
    )
    action = forms.ChoiceField(choices=ACTION_CHOICES, label="Action")
    extension_days = forms.IntegerField(label="Jours à ajouter", required=False)
    start_date = forms.DateField(
        label="Date de début", required=False, widget=forms.SelectDateWidget
    )
    expiry_date = forms.DateField(
        label="Date d'expiration", required=False, widget=forms.SelectDateWidget
    )


class BulkStatusForm(forms.Form):
    new_status = forms.ChoiceField(choices=License.STATUS, label="Nouveau statut")
