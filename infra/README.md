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
docker compose -f docker-compose.dev.yml up --build

```

Stop:

```

docker compose -f docker-compose.dev.yml down

```

Reset database:

```

docker compose -f docker-compose.dev.yml down -v

```

Backend runs with live reload at:
http://localhost:8000

Database:

localhost:5432\
User: postgres\
Password: postgres

---

## Production Deployment

Production uses external services:

- PostgreSQL = Railway
- Redis = Upstash
- Nginx = Reverse proxy
- Cloudflare = SSL

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

## Architecture

Client → Cloudflare → Nginx → FastAPI
