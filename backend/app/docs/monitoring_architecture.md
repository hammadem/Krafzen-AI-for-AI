# KRAFZEN Queue Monitoring & Logging Architecture
**Owner:** Tazwar  
**Week 1 Deliverable — Step 6**  
**Status:** Foundation defined; instrumentation expands in Week 3

---

## 1. Logging Stack

The project uses **structlog** (JSON renderer) over stdlib logging, initialized in `core/logging_config.py`. All queue and service logs go through `utils/logger.py`:

```python
from app.utils.logger import logger
logger.info("event description", key=value, ...)
```

All log calls must use keyword arguments for structured fields — never f-string interpolation into the message body.

---

## 2. Queue Log Standards

Every queue operation in `queue_service.py` and `job_routes.py` must emit structured logs at these points:

| Event | Level | Required Fields |
|---|---|---|
| Job enqueued | `INFO` | `job_id`, `project_id` |
| Transition attempted | `INFO` | `job_id`, `from_status`, `to_status` |
| Invalid transition blocked | `WARNING` | `job_id`, `from_status`, `to_status`, `allowed` |
| Non-contract status detected | `ERROR` | `job_id`, `current_status` |
| Transition succeeded | `INFO` | `job_id`, `from_status`, `to_status` |
| Job not found / unauthorized | `WARNING` | `job_id` |
| Retry attempted | `INFO` | `job_id`, `from_status` |
| Retry blocked (non-retryable) | `WARNING` | `job_id`, `current_status` |

These are already implemented in `queue_service.py`. This document locks them as the standard.

---

## 3. Monitoring Tags (for Week 3 instrumentation)

When metrics infrastructure is added in Week 3, every queue event should carry these tags:
- krafzen.queue.job_id
- krafzen.queue.project_id
- krafzen.queue.from_status
- krafzen.queue.to_status
- krafzen.queue.event_type   # enqueue | advance | retry | cancel
- krafzen.queue.outcome      # success | blocked | error

---

## 4. Failure Categories to Track

| Failure Type | Detection Method | Week 3 Action |
|---|---|---|
| Invalid transition | `WARNING` log in `advance_job_status` | Counter metric |
| Non-contract status (pre-migration rows) | `ERROR` log in `advance_job_status` | Alert threshold |
| Job not found / unauthorized | `WARNING` in queue_service | Counter per route |
| Retry of non-retryable state | `WARNING` in `retry_job` | Counter metric |
| DB update failure (update_job returns error) | `WARNING` in queue_service | Alert on spike |
| Stuck jobs (queued/processing > N minutes) | Not yet implemented | Week 3: scheduled reaper |

---

## 5. Sentry Integration

Sentry is initialized in `core/logging_config.py` via `init_sentry()`. Current behavior:

- `logging.ERROR` and above → Sentry event
- `logging.INFO` and above → Sentry breadcrumb
- `traces_sample_rate=1.0` (full tracing — reduce to 0.1 before production)

Queue failures that should always create Sentry events:
- Non-contract status detected on a live job (migration not applied)
- DB `update_job` returns an error dict (unexpected Supabase failure)

To manually capture in Week 3:
```python
import sentry_sdk
sentry_sdk.capture_message("Stuck job detected", level="warning", extras={"job_id": job_id})
```

---

## 6. Stuck Job Detection (Week 3 Scope)

A job is "stuck" if it remains in `queued` or `processing` for longer than a configurable threshold (default: 10 minutes). Week 3 will implement a background reaper that:

1. Queries jobs WHERE status IN ('queued', 'processing') AND updated_at < NOW() - INTERVAL
2. Transitions them to `failed` with `error_message = "Job timed out — auto-failed by reaper"`
3. Emits a `WARNING` log and Sentry event per stuck job
4. Exposes a `GET /api/v1/dashboard/queue-health` endpoint (Week 3)

---

## 7. Dead-Letter Queue (DLQ) Preparation

There is no external message broker in Week 1. The DLQ equivalent is:

- Jobs that fail and are not retried within 24h → surfaced in `requires_attention` count on workspace summary
- Week 3 will add a `failed_at` column and a `GET /api/v1/jobs?status=failed&stale=true` query for admin review

---

## 8. What Is NOT in Scope for Week 1

- External metrics (Datadog, Prometheus) — Week 3
- Stuck-job reaper — Week 3
- Queue depth monitoring — Week 3
- Alert thresholds — Week 3
- Tracing spans — Week 3