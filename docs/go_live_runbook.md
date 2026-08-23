# Pratiraksha Go-Live Runbook

## Pre-Flight Checklist
- `[ ]` Ensure Sentry DSN is correctly configured in production environment variables.
- `[ ]` Ensure Redis caching backend is fully operational and authenticated.
- `[ ]` Ensure Postgres DB connection pool options (`POOL_SIZE`, `MAX_OVERFLOW`) are correctly sized for Gunicorn and Celery workers.
- `[ ]` Validate that all SSO keys (Google, GitHub) are populated.

## Step 1: Database Migrations
```bash
python manage.py migrate --noinput
```
*Note: Verify that `activity_logs` and `compliance_logs` MongoDB indices are also built (if required).*

## Step 2: Static Assets
```bash
python manage.py collectstatic --noinput
```

## Step 3: Application Services Start
1. **Daphne (ASGI)**: Handles WebSockets for realtime updates.
   ```bash
   daphne -b 0.0.0.0 -p 8001 pratiraksha.asgi:application
   ```
2. **Gunicorn (WSGI)**: Handles standard REST API traffic.
   ```bash
   gunicorn pratiraksha.wsgi:application --workers 4 --threads 4 -b 0.0.0.0:8000
   ```
3. **Celery**: Background workers for Webhooks, ML pipelines, and Report generation.
   ```bash
   celery -A pratiraksha worker -l INFO
   ```

## Step 4: Verification
- Ping `/api/v1/auth/login/` (Expect 400/405).
- Check Sentry dashboard for any unhandled exceptions during boot.

## Rollback Procedure
If critical failures occur within 5 minutes of go-live:
1. Revert deployment container/VM to the previous image tag.
2. Stop new celery queues to prevent broken tasks from piling up.
3. If database corruption occurred, initiate emergency restore from the nearest RPO snapshot (see Disaster Recovery section).
