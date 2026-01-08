from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('license-app/', include('license_app.urls', namespace='license_app')),
]
