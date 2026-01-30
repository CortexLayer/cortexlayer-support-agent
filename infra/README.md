# CortexLayer Infrastructure

This repository uses two separate Docker Compose configurations:

- `docker-compose.dev.yml` → Local development
- `docker-compose.yml` → Production deployment

Do NOT run the development compose on production servers.

---

## Local Development

Prerequisites:
- Docker
- Python 3.10

Start containers:

```bash
cd infra
docker compose -f docker-compose.dev.yml up --build -d
````

Stop:

```bash
docker compose -f docker-compose.dev.yml down
```

Reset database:

```bash
docker compose -f docker-compose.dev.yml down -v
```

Logs:

```bash
docker compose logs -f
```

Backend runs with live reload at:
[http://localhost:8000](http://localhost:8000)

Database:

* Host: localhost
* Port: 5433
* User: postgres
* Password: postgres

---

## Production Deployment

Production uses external managed services:

* PostgreSQL = Railway
* Redis = Upstash
* Nginx = Reverse proxy
* Cloudflare = SSL / DNS

Start services:

```bash
cd infra
docker compose up -d
```

Stop services:

```bash
docker compose down
```

Logs:

```bash
docker compose logs -f
```

---

## Scheduled Jobs (Billing & Enforcement)

CortexLayer relies on scheduled background jobs for billing enforcement
and account lifecycle management.

These jobs **DO NOT run automatically** as part of the API
and **ARE NOT self-scheduling**.

---

### Daily Billing – Overage Enforcement

**Frequency:** Daily

* Checks monthly usage per client
* Bills usage beyond soft cap (plan limit + 20%)
* Disables client access after hard cap (plan limit + 50%)

---

### Daily Billing – Grace Period Enforcement

**Frequency:** Daily

* Identifies clients in `GRACE_PERIOD`
* Disables accounts after 7 days without successful payment

---

### Scheduler Execution Model

Billing and enforcement logic is packaged in a dedicated container
named `scheduler`.

The scheduler:

* Executes **once**
* Performs a full billing + enforcement pass
* Exits cleanly

---

### Production Requirement

In production, the scheduler **MUST be triggered by host-level cron**.

Example:

```cron
0 2 * * * cd /srv/cortexlayer/infra && docker compose run --rm scheduler >> /var/log/cortexlayer-scheduler.log 2>&1
```

Docker Compose **does not provide scheduling**.
Without host cron, billing will only run once (at deploy time).

---

## Architecture

Client → Cloudflare → Nginx → FastAPI
Scheduler → PostgreSQL + Redis (independent of API)