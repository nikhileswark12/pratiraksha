import datetime
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    return JsonResponse({
        "status": "ok",
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

def ready_check(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
        
    if db_ok:
        return JsonResponse({
            "status": "ready",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    else:
        return JsonResponse({
            "status": "not_ready",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }, status=503)
