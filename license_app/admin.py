from datetime import timedelta
import csv

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import format_html

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import License, Product, Customer, ClientType
from .forms import BulkUpdateDatesForm, SetProductForm


class LicenseResource(resources.ModelResource):
    class Meta:
        model = License
        fields = (
            'id',
            'license_number',
            'customer',
            'product',
            'start_date',
            'expiry_date',
            'status',
            'comment',
            'created_at',
            'updated_at',
        )
        export_order = fields
        import_id_fields = ['license_number']
        skip_unchanged = True
        report_skipped = True


def set_product(modeladmin, request, queryset):
    if 'apply' in request.POST:
        form = SetProductForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['new_product']
            updated = 0

            for license in queryset:
                license.product = product
                license.save()
                updated += 1

            messages.success(
                request,
                f"✅ {updated} licence(s) mise(s) à jour avec le produit « {product} »."
            )
            return None
    else:
        form = SetProductForm()

    return render(request, 'admin/license_app/set_product_form.html', {
        'form': form,
        'queryset': queryset,
        'action_checkbox_name': ACTION_CHECKBOX_NAME,
        'opts': modeladmin.model._meta,
        'title': "Modifier le produit en masse",
    })

set_product.short_description = "📝 Modifier le produit"

def bulk_update_dates(modeladmin, request, queryset):
    if 'apply' in request.POST:
        form = BulkUpdateDatesForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            updated = 0

            if action == 'extend':
                days = form.cleaned_data['extension_days']
                for license in queryset:
                    if license.expiry_date:
                        license.expiry_date += timedelta(days=days)
                        license.save()
                        updated += 1
                messages.success(request, f"✅ {updated} licence(s) prolongée(s) de {days} jours.")

            elif action == 'set_start':
                start_date = form.cleaned_data['start_date']
                updated = queryset.update(start_date=start_date)
                messages.success(request, f"✅ {updated} licence(s) mise(s) à jour.")

            elif action == 'set_expiry':
                expiry_date = form.cleaned_data['expiry_date']
                updated = queryset.update(expiry_date=expiry_date)
                messages.success(request, f"✅ {updated} licence(s) mise(s) à jour.")

            return None
    else:
        form = BulkUpdateDatesForm()

    return render(request, 'admin/license_app/bulk_update_dates_form.html', {
        'form': form,
        'queryset': queryset,
        'action_checkbox_name': ACTION_CHECKBOX_NAME,
        'opts': modeladmin.model._meta,
        'title': "Gestion des dates en masse",
    })

bulk_update_dates.short_description = "📅 Gérer les dates"


def bulk_change_status(modeladmin, request, queryset):
    if 'apply' in request.POST:
        form = BulkStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['new_status']
            comment = form.cleaned_data.get('comment')
            updated = 0

            for license in queryset:
                license.status = status
                if comment:
                    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                    license.comment = (license.comment or '') + f"\n[{timestamp}] {comment}"
                license.save()
                updated += 1

            messages.success(request, f"✅ {updated} licence(s) mise(s) à jour.")
            return None
    else:
        form = BulkStatusForm()

    return render(request, 'admin/license_app/bulk_status_form.html', {
        'form': form,
        'queryset': queryset,
        'action_checkbox_name': ACTION_CHECKBOX_NAME,
        'opts': modeladmin.model._meta,
        'title': "Changer le statut",
    })

bulk_change_status.short_description = "🔄 Changer le statut"


def activate_licenses(modeladmin, request, queryset):
    for license in queryset:
        license.status = 'active'
        license.save()
    messages.success(request, "✅ Licences activées.")

activate_licenses.short_description = "✅ Activer"


def suspend_licenses(modeladmin, request, queryset):
    for license in queryset:
        license.status = 'suspended'
        license.save()
    messages.warning(request, "⚠️ Licences suspendues.")

suspend_licenses.short_description = "⏸️ Suspendre"

def export_selected_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="licences_{timezone.now():%Y%m%d_%H%M%S}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'Numéro', 'Client', 'Produit', 'Début', 'Expiration', 'Statut', 'Jours restants'
    ])

    queryset = queryset.select_related('product')

    for license in queryset:
        writer.writerow([
            license.license_number,
            license.customer,
            license.product,
            license.start_date,
            license.expiry_date,
            license.get_status_display(),
            license.days_until_expiry() or 'N/A',
        ])

    return response

export_selected_to_csv.short_description = "📥 Exporter en CSV"


@admin.register(License)
class LicenseAdmin(ImportExportModelAdmin):
    resource_class = LicenseResource

    list_display = (
        'license_number_display',
        'customer',
        'product',
        'start_date',
        'expiry_date_display',
        'status_badge',
        'expiry_status',
        'created_at',
    )

    list_filter = (
        'status',
        'product',
        ('expiry_date', admin.DateFieldListFilter),
    )

    search_fields = (
        'license_number',
        'customer',
        'product__name',
        'comment',
    )

    ordering = ('-expiry_date',)
    date_hierarchy = 'expiry_date'
    readonly_fields = ('created_at', 'updated_at', 'expiry_status')

    actions = [
        set_product,
        bulk_update_dates,
        bulk_change_status,
        activate_licenses,
        suspend_licenses,
        export_selected_to_csv,
    ]

    fieldsets = (
        ('📋 Informations', {'fields': ('license_number', 'customer', 'product')}),
        ('📅 Dates', {'fields': ('start_date', 'expiry_date', 'expiry_status')}),
        ('🔄 Statut', {'fields': ('status', 'comment')}),
        ('ℹ️ Métadonnées', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


    def license_number_display(self, obj):
        return format_html('<strong style="color:#417690;">{}</strong>', obj.license_number)
    license_number_display.short_description = "Licence"

    def expiry_date_display(self, obj):
        days = obj.days_until_expiry()
        if days is None:
            return format_html('<span style="color:#999;">Non définie</span>')
        if days < 0:
            color = '#dc3545'
        elif days <= 30:
            color = '#fd7e14'
        else:
            return obj.expiry_date
        return format_html('<strong style="color:{};">{}</strong>', color, obj.expiry_date)
    expiry_date_display.admin_order_field = 'expiry_date'

    def status_badge(self, obj):
        colors = {
            'active': '#28a745',
            'expired': '#dc3545',
            'suspended': '#ffc107',
            'pending': '#17a2b8',
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:3px;font-size:11px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display(),
        )
    status_badge.short_description = "Statut"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)




@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'client_type')
    search_fields = ('name', 'email')
    list_filter = ('client_type',)

@admin.register(ClientType)
class ClientTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
