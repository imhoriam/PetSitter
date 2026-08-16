from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")), # Activează login/logout în Browsable API
    path("api/", include("marketplace.urls")),
]