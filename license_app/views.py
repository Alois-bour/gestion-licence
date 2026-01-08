from datetime import timedelta

import pandas as pd
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from .models import (
    CategorieUtilisateur,
    Customer,
    Editeur,
    Entite,
    License,
    Product,
    Service,
)


@staff_member_required
def reporting_dashboard(request):
    today = timezone.now().date()

    # --- Data Aggregation ---

    # By Editor
    editors_stats = Editeur.objects.annotate(
        total_licenses=Count("product__license"),
        active_licenses=Count(
            "product__license", filter=Q(product__license__status="active")
        ),
        expired_licenses=Count(
            "product__license", filter=Q(product__license__status="expired")
        ),
        expiring_soon=Count(
            "product__license",
            filter=Q(
                product__license__expiry_date__lte=today + timedelta(days=90),
                product__license__expiry_date__gte=today,
            ),
        ),
    ).order_by("-total_licenses")

    # By Product
    products_stats = Product.objects.annotate(
        total_licenses=Count("license"),
    ).order_by("-total_licenses")

    # Expiry Analysis
    expired_licenses = License.objects.filter(status="expired")
    expiring_in_30_days = License.objects.filter(
        expiry_date__lte=today + timedelta(days=30), expiry_date__gte=today
    )
    expiring_in_60_days = License.objects.filter(
        expiry_date__lte=today + timedelta(days=60),
        expiry_date__gt=today + timedelta(days=30),
    )
    expiring_in_90_days = License.objects.filter(
        expiry_date__lte=today + timedelta(days=90),
        expiry_date__gt=today + timedelta(days=60),
    )

    # By Entity and Service
    entities_stats = Entite.objects.annotate(total_licenses=Count("license")).order_by(
        "-total_licenses"
    )
    services_stats = Service.objects.annotate(total_licenses=Count("license")).order_by(
        "-total_licenses"
    )

    context = {
        "editors_stats": editors_stats,
        "products_stats": products_stats,
        "expired_licenses": expired_licenses,
        "expiring_in_30_days": expiring_in_30_days,
        "expiring_in_60_days": expiring_in_60_days,
        "expiring_in_90_days": expiring_in_90_days,
        "entities_stats": entities_stats,
        "services_stats": services_stats,
    }

    return render(request, "admin/reporting_dashboard.html", context)


@staff_member_required
def import_with_mapping(request):
    if request.method == "POST":
        if "file" in request.FILES:
            file = request.FILES["file"]

            # File validation
            if not file.name.endswith((".xls", ".xlsx")):
                messages.error(
                    request, "Invalid file type. Please upload an Excel file."
                )
                return render(request, "admin/import_mapping.html")

            if file.size > 5 * 1024 * 1024:  # 5MB
                messages.error(request, "File is too large. Maximum size is 5MB.")
                return render(request, "admin/import_mapping.html")

            try:
                df = pd.read_excel(file)
                headers = df.columns.tolist()
                request.session["import_df"] = df.to_json()
                request.session["headers"] = headers

                # Get all fields, including foreign keys
                model_fields = [
                    f.name for f in License._meta.get_fields() if not f.auto_created
                ]
                # Manually add related fields needed for lookups during import
                model_fields.append("editeur")
                model_fields.sort()

                return render(
                    request,
                    "admin/import_mapping.html",
                    {"headers": headers, "model_fields": model_fields},
                )
            except Exception as e:
                messages.error(request, f"Error reading the file: {e}")

        elif "mapping" in request.POST:
            df_json = request.session.get("import_df")
            headers = request.session.get("headers")

            if df_json and headers:
                df = pd.read_json(df_json)
                success_count = 0
                error_count = 0
                errors = []

                for index, row in df.iterrows():
                    try:
                        license_data = {}
                        for i, header in enumerate(headers):
                            field_name = request.POST.get(f"mapping-{i}")
                            if field_name:
                                license_data[field_name] = row[header]

                        # Handle foreign keys
                        # --- Handle Foreign Keys ---

                        # Product requires special handling due to its dependency on Editeur
                        if "product" in license_data and "editeur" in license_data:
                            editor_name = license_data.pop("editeur")
                            product_name = license_data.pop("product")

                            if editor_name and product_name:
                                editor, _ = Editeur.objects.get_or_create(
                                    name=editor_name
                                )
                                product, _ = Product.objects.get_or_create(
                                    name=product_name, editeur=editor
                                )
                                license_data["product"] = product
                            else:
                                raise ValueError("Product and Editeur are required.")

                        # Handle other simple Foreign Keys
                        fk_fields = {
                            "customer": Customer,
                            "entite": Entite,
                            "service": Service,
                            "categorie_utilisateur": CategorieUtilisateur,
                        }
                        for field, model in fk_fields.items():
                            if field in license_data and license_data[field]:
                                obj, _ = model.objects.get_or_create(
                                    name=license_data[field]
                                )
                                license_data[field] = obj

                        License.objects.create(**license_data)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {index + 1}: {e}")

                messages.success(
                    request, f"{success_count} licenses imported successfully."
                )
                if error_count > 0:
                    messages.error(request, f"{error_count} licenses failed to import.")
                    for error in errors:
                        messages.warning(request, error)

                del request.session["import_df"]
                del request.session["headers"]

    return render(request, "admin/import_mapping.html")
