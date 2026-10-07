"""
URL configuration for pratiraksha project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from pratiraksha.views import health_check, ready_check

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('health/', health_check),
    path('ready/', ready_check),
    path('sentry-debug/', trigger_error),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/hospitals/', include('hospitals.urls')),
    path('api/v1/predictions/', include('predictions.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    path('api/v1/crisis/', include('crisis.urls')),
    path('api/v1/ehr/', include('ehr.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    
    # API v2
    path('api/v2/', include('pratiraksha.urls_v2')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
