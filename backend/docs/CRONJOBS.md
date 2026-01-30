# CortexLayer Scheduled Jobs

This document defines all scheduled background jobs required for correct
billing enforcement and account lifecycle management.

These jobs MUST run independently of API requests.
They are executed via a dedicated scheduler entrypoint and triggered
by host-level cron in production.

---

## 1. Daily Billing & Enforcement Job

### Purpose

Runs the following critical operations:

1. Detects monthly query overages
2. Bills overages via Stripe invoice items
3. Enforces hard caps (150%)
4. Enforces grace-period expiration
5. Disables delinquent accounts

---

### Entry Point

```bash
python -m backend.app.services.scheduler
````

This command is **idempotent** and safe to run multiple times.
It performs a single full billing + enforcement pass and then exits.

---

## Execution Model

### Local Development

In development, the scheduler is executed **manually**:

```bash
docker compose run --rm scheduler
```

This avoids unintended billing actions during development
and allows controlled testing.

---

### Production

In production, the scheduler **MUST be triggered by host-level cron**.

Example crontab entry:

```cron
0 2 * * * cd /srv/cortexlayer/infra && docker compose run --rm scheduler >> /var/log/cortexlayer-scheduler.log 2>&1
```

This ensures:

* Daily execution
* Predictable billing windows
* Durable logs
* Safe retries on failure

⚠️ Docker Compose **does NOT provide scheduling**.
The scheduler container runs only when explicitly executed.

---

## Failure Handling

* Stripe failures are logged and do not corrupt billing state
* Database failures abort execution safely
* Partial execution is prevented via transactional boundaries