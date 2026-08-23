# Pratiraksha API v2 & Integration Guide

Welcome to the Pratiraksha Integration Guide. This document outlines how partner and government systems can integrate with the Pratiraksha Hospital Network Capacity Management Platform using our API v2 and Webhook system.

## REST API v2

The Pratiraksha REST API v2 is an additive versioned layer introduced to provide backward compatibility for v1 clients (web/mobile apps) while offering a stable integration surface for third parties.

**Base URL:** `https://api.pratiraksha.com/api/v2/`

### Authentication
API v2 endpoints enforce authentication. Clients must authenticate via JWT by sending their access token in the Authorization header:
```
Authorization: Bearer <your-access-token>
```
To obtain a token, contact the system administrator to provision a service account.

## Webhook System

Pratiraksha can push real-time events to your systems using Webhooks. This allows you to react immediately to critical events without needing to poll our APIs.

### Supported Events

1. **`hospital.status_changed`**
   Fired when a hospital's status escalates or de-escalates (e.g., from NORMAL to CRITICAL).
2. **`crisis.alert_created`**
   Fired when a crisis simulation or alert is generated affecting the hospital network.

### Subscribing to Webhooks
To subscribe, contact a Pratiraksha administrator to register your `WebhookEndpoint`. You will receive a unique cryptographic **Secret** used to verify payloads.

### Payload Structure & Verification

Every webhook payload is sent as an HTTP POST request with `Content-Type: application/json`.
We include a signature in the `X-Pratiraksha-Signature` header to ensure the payload was not tampered with.

**Header Example:**
```
X-Pratiraksha-Event: hospital.status_changed
X-Pratiraksha-Signature: sha256=d3b07384d113edec49eaa6238ad5ff00
```

You must compute the HMAC SHA-256 signature of the raw request body using your assigned secret and compare it to the `X-Pratiraksha-Signature` header.

### Real Payload Examples

#### 1. `hospital.status_changed`
```json
{
  "hospital_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
  "old_status": "NORMAL",
  "new_status": "CRITICAL",
  "timestamp": "2026-08-14 08:35:00+00:00"
}
```

#### 2. `crisis.alert_created`
```json
{
  "simulation_id": "sim_84f93a1c-9b2e-43a1-8d2b-6c4a8f9d3e71",
  "scenario": "smog_alert",
  "affected_hospitals": ["a1b2c3d4-e5f6-7890-1234-56789abcdef0"],
  "estimated_patient_surge": 120,
  "department_breakdown": {
    "Pulmonology": 60,
    "ER": 30,
    "Pediatrics": 10
  },
  "response_plan": {
    "recommended_actions": [
      "Stock up on oxygen cylinders",
      "Alert Pulmonologists on call",
      "Prepare nebulizers in ER"
    ],
    "resource_reallocation_suggestions": [
      {
        "from": "General Ward",
        "to": "ER",
        "item": "Staff Nurses",
        "count": 2
      }
    ]
  },
  "timestamp": "2026-08-14T08:35:00.000Z"
}
```
