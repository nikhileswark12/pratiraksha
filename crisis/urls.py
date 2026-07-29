from django.urls import path
from .views import CrisisSimulationView

urlpatterns = [
    path('simulate/', CrisisSimulationView.as_view(), name='crisis-simulate'),
]
