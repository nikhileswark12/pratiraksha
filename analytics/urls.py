from django.urls import path
from .views import AnalyticsOverviewView, AnalyticsTrendsView, AnalyticsCompareView, ReportRequestView, ReportStatusView

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('trends/', AnalyticsTrendsView.as_view(), name='analytics-trends'),
    path('compare/', AnalyticsCompareView.as_view(), name='analytics-compare'),
    path('report/', ReportRequestView.as_view(), name='report-request'),
    path('report/<uuid:report_id>/', ReportStatusView.as_view(), name='report-status'),
]
