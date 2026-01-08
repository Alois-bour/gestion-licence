import pandas as pd
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import License, Customer, Product
from django.contrib import messages

@staff_member_required
def import_with_mapping(request):
    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']

            # File validation
            if not file.name.endswith(('.xls', '.xlsx')):
                messages.error(request, "Invalid file type. Please upload an Excel file.")
                return render(request, 'admin/import_mapping.html')

            if file.size > 5 * 1024 * 1024: # 5MB
                messages.error(request, "File is too large. Maximum size is 5MB.")
                return render(request, 'admin/import_mapping.html')

            try:
                df = pd.read_excel(file)
                headers = df.columns.tolist()
                request.session['import_df'] = df.to_json()
                request.session['headers'] = headers

                # Get all fields, including foreign keys
                model_fields = [f.name for f in License._meta.get_fields() if not f.auto_created]

                return render(request, 'admin/import_mapping.html', {
                    'headers': headers,
                    'model_fields': model_fields
                })
            except Exception as e:
                messages.error(request, f"Error reading the file: {e}")

        elif 'mapping' in request.POST:
            mapping = {key: value for key, value in request.POST.items() if key.startswith('mapping-')}
            df_json = request.session.get('import_df')
            headers = request.session.get('headers')

            if df_json and headers:
                df = pd.read_json(df_json)
                success_count = 0
                error_count = 0
                errors = []

                for index, row in df.iterrows():
                    try:
                        license_data = {}
                        for i, header in enumerate(headers):
                            field_name = request.POST.get(f'mapping-{i}')
                            if field_name:
                                license_data[field_name] = row[header]

                        # Handle foreign keys
                        if 'customer' in license_data:
                            customer, _ = Customer.objects.get_or_create(name=license_data['customer'])
                            license_data['customer'] = customer
                        if 'product' in license_data:
                            product, _ = Product.objects.get_or_create(name=license_data['product'])
                            license_data['product'] = product

                        License.objects.create(**license_data)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {index + 1}: {e}")

                messages.success(request, f"{success_count} licenses imported successfully.")
                if error_count > 0:
                    messages.error(request, f"{error_count} licenses failed to import.")
                    for error in errors:
                        messages.warning(request, error)

                del request.session['import_df']
                del request.session['headers']

    return render(request, 'admin/import_mapping.html')
