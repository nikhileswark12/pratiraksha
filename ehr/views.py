from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from hospitals.models import Hospital
from .models import (
    Patient, Encounter, Vital, Diagnosis, Prescription, 
    LabResult, EHRAccessLog, DischargeSummary
)
from .serializers import (
    PatientSerializer, EncounterSerializer, VitalSerializer,
    DiagnosisSerializer, PrescriptionSerializer, LabResultSerializer
)
from .tasks import generate_discharge_summary

def log_ehr_access(hospital_id, patient_id, actor, action, resource_type, resource_id):
    EHRAccessLog.objects.create(
        hospital_id=hospital_id,
        patient_id=patient_id,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id
    )

class PatientCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'hospital_manager':
            return Response({"error": "Forbidden: Only hospital managers can access EHR data."}, status=status.HTTP_403_FORBIDDEN)
            
        hospital = request.user.hospital
        if not hospital:
            return Response({"error": "User is not assigned to a hospital."}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            # Generate MRN
            seq = Patient.objects.filter(hospital=hospital).count() + 1
            hospital_code = str(hospital.id)[:4].upper()
            mrn = f"PRX-{hospital_code}-{seq:06d}"
            
            patient = serializer.save(hospital=hospital, mrn=mrn)
            
            log_ehr_access(
                hospital_id=hospital.id,
                patient_id=patient.id,
                actor=request.user,
                action="create_patient",
                resource_type="Patient",
                resource_id=str(patient.id)
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EncounterCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'hospital_manager':
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
            
        hospital = request.user.hospital
        serializer = EncounterSerializer(data=request.data)
        if serializer.is_valid():
            patient_id = request.data.get('patient')
            try:
                patient = Patient.objects.get(id=patient_id, hospital=hospital)
            except Patient.DoesNotExist:
                return Response({"error": "Patient not found in your hospital."}, status=status.HTTP_404_NOT_FOUND)
                
            encounter = serializer.save(hospital=hospital, patient=patient, status='OPEN')
            
            log_ehr_access(hospital.id, patient.id, request.user, "create_encounter", "Encounter", str(encounter.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EncounterDischargeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role != 'hospital_manager':
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            encounter = Encounter.objects.get(id=pk, hospital=request.user.hospital)
        except Encounter.DoesNotExist:
            return Response({"error": "Encounter not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if encounter.status != 'OPEN':
            return Response({"error": f"Cannot discharge encounter with status {encounter.status}."}, status=status.HTTP_400_BAD_REQUEST)
            
        encounter.status = 'DISCHARGED'
        encounter.discharged_at = timezone.now()
        encounter.save()
        
        log_ehr_access(encounter.hospital.id, encounter.patient.id, request.user, "discharge_encounter", "Encounter", str(encounter.id))
        
        # Enqueue discharge summary task
        summary = DischargeSummary.objects.create(
            hospital=encounter.hospital,
            encounter=encounter,
            requested_by=request.user,
            status='queued'
        )
        generate_discharge_summary.delay(str(summary.id))
        
        return Response({"status": "DISCHARGED", "discharged_at": encounter.discharged_at, "summary_id": str(summary.id)})

class EncounterCloseView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'hospital_manager':
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            encounter = Encounter.objects.get(id=pk, hospital=request.user.hospital)
        except Encounter.DoesNotExist:
            return Response({"error": "Encounter not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if encounter.status != 'DISCHARGED':
            return Response({"error": "Can only close a discharged encounter."}, status=status.HTTP_400_BAD_REQUEST)
            
        encounter.status = 'CLOSED'
        encounter.save()
        log_ehr_access(encounter.hospital.id, encounter.patient.id, request.user, "close_encounter", "Encounter", str(encounter.id))
        return Response({"status": "CLOSED"})

# Clinical endpoints base class to avoid repetition
class BaseClinicalCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None
    resource_name = ""

    def post(self, request, pk):
        if request.user.role != 'hospital_manager':
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            encounter = Encounter.objects.get(id=pk, hospital=request.user.hospital)
        except Encounter.DoesNotExist:
            return Response({"error": "Encounter not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if encounter.status == 'CLOSED':
            return Response({"error": "Cannot add data to a closed encounter."}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            supersedes_id = serializer.validated_data.pop('supersedes_id', None)
            instance = serializer.save(
                hospital=encounter.hospital, 
                encounter=encounter, 
                created_by=request.user
            )
            
            if supersedes_id:
                try:
                    # Generic superseded logic
                    old_instance = self.serializer_class.Meta.model.objects.get(id=supersedes_id, encounter=encounter)
                    old_instance.superseded_by = instance
                    old_instance.save(update_fields=['superseded_by'])
                except self.serializer_class.Meta.model.DoesNotExist:
                    pass
            
            log_ehr_access(encounter.hospital.id, encounter.patient.id, request.user, f"create_{self.resource_name}", self.resource_name, str(instance.id))
            
            return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VitalCreateView(BaseClinicalCreateView):
    serializer_class = VitalSerializer
    resource_name = "Vital"

class DiagnosisCreateView(BaseClinicalCreateView):
    serializer_class = DiagnosisSerializer
    resource_name = "Diagnosis"

class PrescriptionCreateView(BaseClinicalCreateView):
    serializer_class = PrescriptionSerializer
    resource_name = "Prescription"

class LabResultCreateView(BaseClinicalCreateView):
    serializer_class = LabResultSerializer
    resource_name = "LabResult"

class PatientTimelineView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        if request.user.role != 'hospital_manager':
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            patient = Patient.objects.get(id=pk, hospital=request.user.hospital)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)
            
        encounters = Encounter.objects.filter(patient=patient).order_by('-created_at')
        vitals = Vital.objects.filter(encounter__patient=patient).order_by('-recorded_at')
        diagnoses = Diagnosis.objects.filter(encounter__patient=patient, superseded_by__isnull=True).order_by('-created_at')
        prescriptions = Prescription.objects.filter(encounter__patient=patient, superseded_by__isnull=True).order_by('-created_at')
        labs = LabResult.objects.filter(encounter__patient=patient, superseded_by__isnull=True).order_by('-ordered_at')
        
        timeline = []
        for e in encounters:
            timeline.append({"type": "encounter", "data": EncounterSerializer(e).data, "timestamp": e.created_at})
        for v in vitals:
            timeline.append({"type": "vital", "data": VitalSerializer(v).data, "timestamp": v.recorded_at})
        for d in diagnoses:
            timeline.append({"type": "diagnosis", "data": DiagnosisSerializer(d).data, "timestamp": d.created_at})
        for p in prescriptions:
            timeline.append({"type": "prescription", "data": PrescriptionSerializer(p).data, "timestamp": p.created_at})
        for l in labs:
            timeline.append({"type": "lab_result", "data": LabResultSerializer(l).data, "timestamp": l.ordered_at})
            
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return Response({"patient": PatientSerializer(patient).data, "timeline": timeline})

class DischargeSummaryStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, summary_id):
        if request.user.role != 'hospital_manager':
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            summary = DischargeSummary.objects.get(id=summary_id, encounter_id=pk, hospital=request.user.hospital)
        except DischargeSummary.DoesNotExist:
            return Response({"error": "Summary not found."}, status=status.HTTP_404_NOT_FOUND)
            
        response_data = {
            "status": summary.status,
            "created_at": summary.created_at
        }
        
        if summary.status == 'ready' and summary.file:
            response_data["download_url"] = request.build_absolute_uri(summary.file.url)
        elif summary.status == 'failed':
            response_data["error_message"] = summary.error_message
            
        return Response(response_data)

class CapacityFeedView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role == 'hospital_manager':
            if not request.user.hospital:
                return Response({"error": "Forbidden: Hospital manager has no assigned hospital."}, status=status.HTTP_403_FORBIDDEN)
            hospitals = Hospital.objects.filter(id=request.user.hospital.id)
        else:
            hospitals = Hospital.objects.all()
            
        hospitals = hospitals.annotate(
            current_admitted=Count('encounters', filter=Q(encounters__status='OPEN', encounters__encounter_type='IPD')),
            emergency_cases=Count('encounters', filter=Q(encounters__status='OPEN', encounters__encounter_type='EMERGENCY')),
            total_open=Count('encounters', filter=Q(encounters__status='OPEN'))
        )
        
        feed_data = []
        for h in hospitals:
            feed_data.append({
                "hospital_id": str(h.id),
                "hospital_name": h.name,
                "current_admitted": h.current_admitted,
                "emergency_cases": h.emergency_cases,
                "total_open_encounters": h.total_open
            })
            
        # Explicit confirmation: No patient identifiable data is fetched or returned here.
        # This purely runs aggregate COUNT operations grouped by hospital.
        return Response({
            "aggregate_metrics": feed_data
        })
