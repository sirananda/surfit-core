# Surfit Runtime Deployment (Ubuntu 24.04 + Docker Compose)

## 1. Clone repository
```bash
git clone <your-repo-url> surfit
cd surfit
```

## 2. Configure environment
```bash
cp .env.example .env
# edit .env and set strong credentials / URLs
```

## 3. Start stack
```bash
docker compose up -d
```

## 4. Verify
```bash
docker compose ps
docker compose logs -f surfit-api nginx
```

Nginx listens on port `80` and reverse proxies to `surfit-api:8000`.
