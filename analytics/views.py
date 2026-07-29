from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import datetime

from hospitals.models import Hospital
from pratiraksha.utils import get_mongo_db


class AnalyticsOverviewView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 1. Hospital counts by status
        hospitals = Hospital.objects.all()
        total_hospitals = hospitals.count()
        status_counts = list(hospitals.values('status').annotate(count=Count('status')))
        
        status_summary = {
            "CRITICAL": 0,
            "MODERATE": 0,
            "NORMAL": 0
        }
        for item in status_counts:
            if item['status'] in status_summary:
                status_summary[item['status']] = item['count']
                
        # 2. Capacity metrics
        capacity_aggs = hospitals.aggregate(
            total_beds=Sum('total_capacity'),
            current_occupancy=Sum('current_occupancy')
        )
        total_beds = capacity_aggs['total_beds'] or 0
        total_occupancy = capacity_aggs['current_occupancy'] or 0
        avg_occupancy = 0
        if total_beds > 0:
            avg_occupancy = round((total_occupancy / total_beds) * 100, 2)
            
        today_predictions = 0
        week_predictions = 0
        
        db = get_mongo_db()
        if db is not None:
            now = datetime.datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - datetime.timedelta(days=7)
            
            try:
                today_predictions = db.predictions.count_documents({"created_at": {"$gte": today_start}})
                week_predictions = db.predictions.count_documents({"created_at": {"$gte": week_start}})
            except Exception as e:
                return Response({"error": "Failed to query analytics data from MongoDB."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            return Response({"error": "Analytics database unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        return Response({
            "total_hospitals": total_hospitals,
            "status_summary": status_summary,
            "total_beds": total_beds,
            "avg_occupancy_percent": avg_occupancy,
            "predictions_today": today_predictions,
            "predictions_this_week": week_predictions
        })


class AnalyticsTrendsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        metric = request.query_params.get('metric', 'prediction-count')
        group_by = request.query_params.get('groupBy', 'day')
        
        # We only support prediction-count trend for now since we don't have historical occupancy data
        if metric != 'prediction-count':
            return Response({"error": "Only 'prediction-count' metric is currently supported for historical trends."}, status=status.HTTP_400_BAD_REQUEST)
            
        db = get_mongo_db()
        if db is None:
            return Response({"error": "Analytics database unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        now = datetime.datetime.utcnow()
        if group_by == 'day':
            start_date = now - datetime.timedelta(days=7)
            date_format = "%Y-%m-%d"
        elif group_by == 'week':
            start_date = now - datetime.timedelta(weeks=4)
            # MongoDB doesn't have simple week format string in strftime, we approximate by date range
            date_format = "%Y-%U" 
        elif group_by == 'month':
            start_date = now - datetime.timedelta(days=365)
            date_format = "%Y-%m"
        else:
            return Response({"error": "Invalid groupBy parameter."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            pipeline = [
                {"$match": {"created_at": {"$gte": start_date}}},
                {"$project": {
                    "date": {"$dateToString": {"format": date_format, "date": "$created_at"}},
                    "risk_score": 1
                }},
                {"$group": {
                    "_id": "$date",
                    "count": {"$sum": 1},
                    "avg_risk": {"$avg": "$risk_score"}
                }},
                {"$sort": {"_id": 1}}
            ]
            
            results = list(db.predictions.aggregate(pipeline))
            
            # Format output
            formatted_results = [
                {
                    "period": r["_id"],
                    "count": r["count"],
                    "avg_risk": round(r.get("avg_risk", 0), 2)
                } for r in results
            ]
            
            return Response({"results": formatted_results})
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
