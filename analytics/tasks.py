import os
import uuid
import logging
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from .models import Report
from pratiraksha.utils import get_mongo_db
from hospitals.models import Hospital

logger = logging.getLogger(__name__)

@shared_task
def generate_report_task(report_id, hospital_ids, group_by='day'):
    try:
        report = Report.objects.get(id=report_id)
        report.status = 'processing'
        report.save()

        # Connect to MongoDB to get analytics data
        db = get_mongo_db()
        if db is None:
            raise Exception("Cannot connect to MongoDB")

        hospitals = Hospital.objects.filter(id__in=hospital_ids)
        hospital_lookup = {str(h.id): h for h in hospitals}
        
        # Build PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Analytics Report - Grouped by {group_by}", styles['Title']))
        elements.append(Spacer(1, 12))

        for h_id, hospital in hospital_lookup.items():
            elements.append(Paragraph(f"Facility: {hospital.name}", styles['Heading2']))
            elements.append(Paragraph(f"Current Occupancy: {hospital.current_occupancy}% | Status: {hospital.status}", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Fetch prediction data from Mongo for this hospital
            match_stage = {'$match': {'input_data.hospital_id': h_id}}
            group_stage = {'$group': {'_id': f'${group_by}', 'count': {'$sum': 1}}}
            sort_stage = {'$sort': {'_id': 1}}
            
            pipeline = [match_stage, group_stage, sort_stage]
            predictions = list(db.predictions.aggregate(pipeline))

            if predictions:
                data = [['Period', 'Prediction Count']]
                for p in predictions:
                    data.append([str(p['_id']), str(p['count'])])
                
                table = Table(data, hAlign='LEFT')
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("No prediction data available for this facility.", styles['Normal']))
            
            elements.append(Spacer(1, 24))

        # Build document
        doc.build(elements)
        
        # Save to model
        pdf_filename = f"report_{report_id}.pdf"
        report.file.save(pdf_filename, ContentFile(buffer.getvalue()))
        report.status = 'ready'
        report.save()

    except Exception as e:
        logger.error(f"Error generating report {report_id}: {str(e)}")
        try:
            report = Report.objects.get(id=report_id)
            report.status = 'failed'
            report.error_message = str(e)
            report.save()
        except Exception:
            pass
