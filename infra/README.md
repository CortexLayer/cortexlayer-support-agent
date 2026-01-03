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

```

cd infra
docker compose -f docker-compose.dev.yml up --build -d

```

Stop:

```

docker compose -f docker-compose.dev.yml down

```

Reset database:

```

docker compose -f docker-compose.dev.yml down -v

```

Logs:

```

docker compose logs -f

```

Backend runs with live reload at:
http://localhost:8000

Database:

localhost:5432  
User: postgres  
Password: postgres

---

## Production Deployment

Production uses external managed services:

- PostgreSQL = Railway
- Redis = Upstash
- Nginx = Reverse proxy
- Cloudflare = SSL / DNS

Start:

```

cd infra
docker compose up -d

```

Stop:

```

docker compose down

```

Logs:

```

docker compose logs -f

```

---

## Scheduled Jobs (Cron)

CortexLayer relies on scheduled background jobs for billing enforcement
and system maintenance. These jobs do NOT run as part of API requests.

---

### Daily Billing – Overage Enforcement

**Frequency:** Daily

- Checks monthly usage per client
- Bills usage beyond soft cap (plan limit + 20%)
- Disables client access after hard cap (plan limit + 50%)

Uses existing billing and usage data stored in PostgreSQL.

---

### Daily Billing – Grace Period Enforcement

**Frequency:** Daily

- Identifies clients in `GRACE_PERIOD`
- Disables accounts after 7 days without successful payment

---

### Database Backups

**Frequency:** Daily (recommended)

- Dumps PostgreSQL database
- Uploads backup to object storage (e.g. S3)
- Retains last 7 days of backups

Backup script:

```

backend/scripts/backup_db.sh

```