from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import License

@login_required
def dashboard(request):
    """
    Dashboard for logged-in users to view their assigned licenses.
    """
    # A user can be associated with multiple customers
    licenses = License.objects.filter(customer__users=request.user).select_related('product', 'customer').order_by('expiry_date')

    return render(request, 'license_app/dashboard.html', {'licenses': licenses})
