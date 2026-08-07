import logging
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .models import DischargeSummary, Diagnosis, Prescription, Vital

logger = logging.getLogger(__name__)

@shared_task
def generate_discharge_summary(summary_id):
    try:
        summary = DischargeSummary.objects.get(id=summary_id)
        summary.status = 'processing'
        summary.save(update_fields=['status'])

        encounter = summary.encounter
        patient = encounter.patient
        hospital = encounter.hospital
        
        # Build PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Discharge Summary", styles['Title']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(f"Facility: {hospital.name}", styles['Heading2']))
        elements.append(Paragraph(f"Patient Name: {patient.name}", styles['Normal']))
        elements.append(Paragraph(f"MRN: {patient.mrn}", styles['Normal']))
        elements.append(Paragraph(f"Admitted: {encounter.admitted_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        if encounter.discharged_at:
            elements.append(Paragraph(f"Discharged: {encounter.discharged_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Diagnoses
        elements.append(Paragraph("Final Diagnoses", styles['Heading3']))
        diagnoses = Diagnosis.objects.filter(encounter=encounter, superseded_by__isnull=True).order_by('-created_at')
        if diagnoses:
            for d in diagnoses:
                primary_flag = " (Primary)" if d.is_primary else ""
                elements.append(Paragraph(f"• {d.icd10_code}: {d.description}{primary_flag}", styles['Normal']))
        else:
            elements.append(Paragraph("No diagnoses recorded.", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Prescriptions
        elements.append(Paragraph("Discharge Medications", styles['Heading3']))
        prescriptions = Prescription.objects.filter(encounter=encounter, superseded_by__isnull=True).order_by('-created_at')
        if prescriptions:
            for p in prescriptions:
                elements.append(Paragraph(f"• {p.medication_name} - {p.dosage} - {p.frequency} (for {p.duration_days} days)", styles['Normal']))
        else:
            elements.append(Paragraph("No medications prescribed.", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Vitals trend (latest)
        elements.append(Paragraph("Latest Vitals", styles['Heading3']))
        latest_vital = Vital.objects.filter(encounter=encounter).order_by('-recorded_at').first()
        if latest_vital:
            elements.append(Paragraph(f"BP: {latest_vital.blood_pressure} | HR: {latest_vital.heart_rate} | Temp: {latest_vital.temperature} | O2: {latest_vital.spo2}", styles['Normal']))
        else:
            elements.append(Paragraph("No vitals recorded.", styles['Normal']))

        # Build document
        doc.build(elements)
        
        # Save to model
        pdf_filename = f"discharge_summary_{summary_id}.pdf"
        summary.file.save(pdf_filename, ContentFile(buffer.getvalue()))
        summary.status = 'ready'
        summary.save()

    except Exception as e:
        logger.error(f"Error generating discharge summary {summary_id}: {str(e)}")
        try:
            summary = DischargeSummary.objects.get(id=summary_id)
            summary.status = 'failed'
            summary.error_message = str(e)
            summary.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
