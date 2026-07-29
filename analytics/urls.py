from django.urls import path
from .views import AnalyticsOverviewView, AnalyticsTrendsView

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('trends/', AnalyticsTrendsView.as_view(), name='analytics-trends'),
]
