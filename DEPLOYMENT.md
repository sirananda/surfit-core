# Surfit Runtime Deployment (Hetzner Ubuntu 24.04)

## 1) Pull latest code

```bash
cd /root/surfit
git pull --ff-only origin main
```

## 2) Configure production env

```bash
cd /root/surfit
cp .env.example .env
nano .env
```

Required values to replace before launch:

- `SURFIT_TOKEN_SECRET`
- `SURFIT_API_KEYS_JSON`
- `SURFIT_DEFAULT_TENANT_ID` (must not be `tenant_demo`)
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `REDIS_URL`

## 3) Start stack

```bash
cd /root/surfit
docker compose up -d --build
docker compose ps
```

## 4) Health verification

```bash
curl -fsS http://localhost/healthz && echo
curl -fsS http://localhost/readyz && echo
```

## 5) Firewall baseline

```bash
cd /root/surfit
bash scripts/ops/setup_ufw.sh
```

Rollback from Hetzner console if lockout occurs:

```bash
ufw disable
```

## 6) PostgreSQL backup baseline

```bash
cd /root/surfit
bash scripts/ops/postgres_backup.sh
bash scripts/ops/install_postgres_backup_cron.sh
```

## 7) HTTPS readiness (domain + Let's Encrypt)

1. Point your domain A record to server IP `46.62.145.237`.
2. Ensure DNS has propagated.
3. Issue cert via certbot container:

```bash
cd /root/surfit
mkdir -p ops/certbot/www ops/certbot/conf
docker run --rm \
  -v /root/surfit/ops/certbot/www:/var/www/certbot \
  -v /root/surfit/ops/certbot/conf:/etc/letsencrypt \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d YOUR_DOMAIN \
  --email YOU@DOMAIN \
  --agree-tos --no-eff-email
```

4. Replace nginx config with HTTPS config:

```bash
cd /root/surfit
cp ops/nginx/https.conf.example nginx.conf
# edit server_name and cert paths if needed
docker compose up -d nginx
```

5. Validate redirect + TLS:

```bash
curl -I http://YOUR_DOMAIN
curl -I https://YOUR_DOMAIN
```

Renewal note:

```bash
docker run --rm \
  -v /root/surfit/ops/certbot/www:/var/www/certbot \
  -v /root/surfit/ops/certbot/conf:/etc/letsencrypt \
  certbot/certbot renew --webroot -w /var/www/certbot
```

After renewal, reload nginx:

```bash
cd /root/surfit
docker compose exec nginx nginx -s reload
```

## 8) Deploy helper

```bash
cd /root/surfit
bash deploy.sh
```
