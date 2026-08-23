from django.urls import path, include

# For now, v2 routes point to the same views as v1.
# This establishes the versioned routing infrastructure additively,
# allowing us to introduce v2-specific views in the future without
# breaking the existing v1 contracts that web/mobile depend on.

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('hospitals/', include('hospitals.urls')),
    path('ehr/', include('ehr.urls')),
    path('predictions/', include('predictions.urls')),
    path('crisis/', include('crisis.urls')),
    path('analytics/', include('analytics.urls')),
]
