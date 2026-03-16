Surfit Canonical Deploy Playbook

Machine/context checks
1) Mac prompt: anda@...
2) Server prompt: root@surfit-mvp:...
3) Server repo path: /root/surfit

Service names
- surfit-api
- nginx
- postgres
- redis

Deploy
cd /root/surfit
git pull origin main
docker-compose up -d postgres redis surfit-api nginx
docker-compose ps

Health checks
curl -fsS http://localhost/healthz && echo
curl -fsS http://localhost/readyz && echo

Runtime checks
curl -s -H "X-Surfit-Tenant-Access: partner_alpha_fixed_key_20260315" http://localhost/api/tenant/dashboard/context | python3 -m json.tool
curl -s -H "X-Surfit-Tenant-Access: partner_alpha_fixed_key_20260315" "http://localhost/api/tenant/dashboard/waves/recent?limit=20" | python3 -m json.tool

Asset marker checks
curl -s http://localhost/tenant-dashboard/ | grep -n "tabTrench"
curl -s http://localhost/tenant-dashboard/dashboard.js | grep -n 'setActiveTab("trench")'

Browser
Open:
http://46.62.145.237/tenant-dashboard?k=partner_alpha_fixed_key_20260315&v=<timestamp>
Then hard refresh once: Shift+Cmd+R
