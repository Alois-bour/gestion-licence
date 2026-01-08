from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.shortcuts import render
from unfold.admin import ModelAdmin

from .forms import BulkStatusForm, BulkUpdateDatesForm, SetProductForm
from .models import (CategorieUtilisateur, ClientType, Customer, Editeur,
                     Entite, License, Product, Service)


def set_product(modeladmin, request, queryset):
    if "apply" in request.POST:
        form = SetProductForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data["new_product"]
            updated = queryset.update(product=product)
            messages.success(request, f"{updated} licences mises à jour.")
            return
    else:
        form = SetProductForm()
    return render(
        request,
        "admin/set_product_form.html",
        {
            "form": form,
            "queryset": queryset,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
        },
    )


set_product.short_description = "Modifier le produit"


def bulk_update_dates(modeladmin, request, queryset):
    if "apply" in request.POST:
        form = BulkUpdateDatesForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            if action == "extend":
                days = form.cleaned_data["extension_days"]
                for license in queryset:
                    if license.expiry_date:
                        license.expiry_date += timedelta(days=days)
                        license.save()
                messages.success(
                    request, f"{queryset.count()} licences prolongées de {days} jours."
                )
            else:
                date = (
                    form.cleaned_data["start_date"]
                    if action == "set_start"
                    else form.cleaned_data["expiry_date"]
                )
                field = "start_date" if action == "set_start" else "expiry_date"
                queryset.update(**{field: date})
                messages.success(request, f"{queryset.count()} licences mises à jour.")
            return
    else:
        form = BulkUpdateDatesForm()
    return render(
        request,
        "admin/bulk_update_dates_form.html",
        {
            "form": form,
            "queryset": queryset,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
        },
    )


bulk_update_dates.short_description = "Gérer les dates"


def bulk_change_status(modeladmin, request, queryset):
    if "apply" in request.POST:
        form = BulkStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data["new_status"]
            queryset.update(status=status)
            messages.success(request, f"{queryset.count()} licences mises à jour.")
            return
    else:
        form = BulkStatusForm()
    return render(
        request,
        "admin/bulk_status_form.html",
        {
            "form": form,
            "queryset": queryset,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
        },
    )


bulk_change_status.short_description = "Changer le statut"


@admin.register(License)
class LicenseAdmin(ModelAdmin):
    list_display = (
        "license_number",
        "product",
        "customer",
        "expiry_date",
        "status",
        "is_expiring_soon",
    )
    list_filter = (
        "status",
        "product__editeur",
        "entite",
        "service",
        "expiry_date",
        "marche_hors_marche",
        "categorie_utilisateur",
    )
    search_fields = (
        "license_number",
        "customer__name",
        "product__name",
        "numero_ej_bdc",
        "numero_commande_sap",
    )
    readonly_fields = ("created_at", "updated_at")
    actions = [set_product, bulk_update_dates, bulk_change_status]
    fieldsets = (
        (
            "Information de base",
            {
                "fields": ("license_number", "product", "customer"),
            },
        ),
        (
            "Détails de la licence",
            {
                "fields": (
                    "type_de_licence",
                    "numero_licence_optionnel",
                    "pack",
                    "identifiant_pack",
                ),
            },
        ),
        (
            "Utilisateurs et Contacts",
            {
                "fields": (
                    "donneur_d_ordre",
                    "end_user_declare",
                    "contact_de_livraison",
                ),
            },
        ),
        (
            "Dates importantes",
            {
                "fields": ("start_date", "expiry_date", "date_de_livraison"),
            },
        ),
        (
            "Informations organisationnelles",
            {
                "fields": ("categorie_utilisateur", "entite", "service", "numero_rio"),
            },
        ),
        (
            "Informations de commande",
            {
                "fields": (
                    "marche_hors_marche",
                    "numero_ej_bdc",
                    "derniere_commande",
                    "date_derniere_commande",
                    "numero_commande_sap",
                    "support",
                ),
            },
        ),
        (
            "Statut et métadonnées",
            {
                "fields": ("status", "remarques", "created_at", "updated_at"),
            },
        ),
    )


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "editeur")
    list_filter = ("editeur",)
    search_fields = ("name",)


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ("name", "client_type", "nom_prenom_contact", "email_contact")
    list_filter = ("client_type",)
    search_fields = ("name", "email_contact")


@admin.register(ClientType)
class ClientTypeAdmin(ModelAdmin):
    search_fields = ("name",)


@admin.register(Editeur)
class EditeurAdmin(ModelAdmin):
    search_fields = ("name",)


@admin.register(Entite)
class EntiteAdmin(ModelAdmin):
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    search_fields = ("name",)


@admin.register(CategorieUtilisateur)
class CategorieUtilisateurAdmin(ModelAdmin):
    search_fields = ("name",)
