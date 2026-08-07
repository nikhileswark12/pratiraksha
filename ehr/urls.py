from django.urls import path
from .views import (
    PatientCreateView, EncounterCreateView, EncounterDischargeView, EncounterCloseView,
    VitalCreateView, DiagnosisCreateView, PrescriptionCreateView, LabResultCreateView,
    PatientTimelineView, DischargeSummaryStatusView, CapacityFeedView
)

urlpatterns = [
    # Patient registration
    path('patients/', PatientCreateView.as_view(), name='patient-create'),
    path('patients/<uuid:pk>/timeline/', PatientTimelineView.as_view(), name='patient-timeline'),
    
    # Encounters
    path('encounters/', EncounterCreateView.as_view(), name='encounter-create'),
    path('encounters/<uuid:pk>/discharge/', EncounterDischargeView.as_view(), name='encounter-discharge'),
    path('encounters/<uuid:pk>/close/', EncounterCloseView.as_view(), name='encounter-close'),
    path('encounters/<uuid:pk>/discharge-summary/<uuid:summary_id>/', DischargeSummaryStatusView.as_view(), name='encounter-discharge-summary'),
    
    # Clinical endpoints (Append-only)
    path('encounters/<uuid:pk>/vitals/', VitalCreateView.as_view(), name='vital-create'),
    path('encounters/<uuid:pk>/diagnoses/', DiagnosisCreateView.as_view(), name='diagnosis-create'),
    path('encounters/<uuid:pk>/prescriptions/', PrescriptionCreateView.as_view(), name='prescription-create'),
    path('encounters/<uuid:pk>/labs/', LabResultCreateView.as_view(), name='lab-create'),
    
    # Operator Feed
    path('hospitals/capacity-feed/', CapacityFeedView.as_view(), name='capacity-feed'),
]
