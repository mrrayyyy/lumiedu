# Huong dan trien khai

## Yeu cau he thong

### Phan cung toi thieu (1-3 hoc sinh dong thoi)
- **CPU:** 4 cores
- **RAM:** 4GB (8GB neu dung Whisper medium + Ollama)
- **Disk:** 10GB (bao gom Docker images + model cache)

### Phan cung khuyen nghi
- **CPU:** 8 cores
- **RAM:** 16GB
- **GPU:** Khong bat buoc (CPU inference OK cho 1-3 users)
- **Disk:** 20GB SSD

### Phan mem
- Docker >= 20.10
- Docker Compose >= 2.0
- Linux (Ubuntu 22.04+ khuyen nghi)

## Trien khai voi Docker Compose

### 1. Chuan bi

```bash
# Clone repository
git clone https://github.com/mrrayyyy/lumiedu.git
cd lumiedu

# Tao va chinh sua cau hinh
cp .env.example .env
```

### 2. Cau hinh production

Sua file `.env`:

```bash
# BAT BUOC thay doi cho production
APP_ENV=production
JWT_SECRET_KEY=<random-string-dai-it-nhat-32-ky-tu>
POSTGRES_PASSWORD=<mat-khau-manh>
DATABASE_URL=postgresql+asyncpg://lumiedu:<mat-khau-manh>@postgres:5432/lumiedu
BOOTSTRAP_ADMIN_PASSWORD=<mat-khau-admin-manh>

# Tuy chon: port
PROXY_PORT=80

# Tuy chon: Ollama (neu co)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:3b

# Tuy chon: Whisper model lon hon (chinh xac hon, can nhieu RAM)
WHISPER_MODEL_SIZE=small
```

### 3. Build va chay

```bash
# Build va khoi dong
docker compose up --build -d

# Kiem tra trang thai (doi ~2 phut)
docker compose ps

# Verify
curl http://localhost/api/health
```

### 4. Xac nhan hoat dong

```bash
# Tat ca 8 containers phai "healthy"
docker compose ps

# Health check
curl http://localhost/api/health
# Expected: {"status":"ok","dependencies":{"postgres":"ok","redis":"ok"}}

# Test login
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lumiedu.local","password":"<mat-khau-admin>"}'
```

## Backup & Restore

### Backup PostgreSQL

```bash
# Backup thu cong
docker compose exec postgres pg_dump -U lumiedu lumiedu > backup_$(date +%Y%m%d).sql

# Hoac dung script co san
bash infra/scripts/backup_postgres.sh
```

### Restore

```bash
# Restore tu file backup
cat backup_20260429.sql | docker compose exec -T postgres psql -U lumiedu lumiedu

# Hoac dung script
bash infra/scripts/restore_postgres.sh backup_20260429.sql
```

### Backup tu dong (cron)

```bash
# Them vao crontab
0 2 * * * cd /path/to/lumiedu && bash infra/scripts/backup_postgres.sh
```

## Cap nhat

```bash
# Lay code moi
git pull origin main

# Rebuild va restart
docker compose up --build -d

# Kiem tra
docker compose ps
curl http://localhost/api/health
```

## Giam sat

### Xem logs

```bash
# Tat ca services
docker compose logs -f

# 1 service cu the
docker compose logs -f api
docker compose logs -f tts-service

# Chi xem errors
docker compose logs -f 2>&1 | grep -i error
```

### Health checks

```bash
# API + dependencies
curl http://localhost/api/health

# Tung service
curl http://localhost:8101/health   # STT
curl http://localhost:8102/health   # LLM
curl http://localhost:8103/health   # TTS
```

### Metrics

```bash
curl http://localhost/metrics
# {"turn_total": 15, "turn_error_total": 1, "e2e_latency_ms_last": 306}
```

## Xu ly su co

### Service bi crash/restart lien tuc

```bash
# Xem logs de tim loi
docker compose logs <service-name> --tail 50

# Restart service
docker compose restart <service-name>
```

### He thong cham

1. Kiem tra RAM: `docker stats`
2. Giam `WHISPER_MODEL_SIZE` xuong `tiny` hoac `base`
3. Giam `MAX_CONCURRENT_SESSIONS`
4. Kiem tra disk space: `df -h`

### Database loi

```bash
# Kiem tra PostgreSQL
docker compose exec postgres psql -U lumiedu -d lumiedu -c "SELECT 1;"

# Restart PostgreSQL
docker compose restart postgres

# Restore tu backup neu can
bash infra/scripts/restore_postgres.sh <backup-file>
```

### Khong truy cap duoc

```bash
# Kiem tra nginx
docker compose logs reverse-proxy

# Kiem tra port
netstat -tlnp | grep 80

# Kiem tra firewall
sudo ufw status
```

## Bao mat production

- [ ] Doi `JWT_SECRET_KEY` thanh random string dai
- [ ] Doi `POSTGRES_PASSWORD` thanh mat khau manh
- [ ] Doi `BOOTSTRAP_ADMIN_PASSWORD`
- [ ] Set `AUTH_DISABLED=false`
- [ ] Cau hinh TLS/SSL (them cert vao nginx)
- [ ] Gioi han CORS origins trong `CORS_ALLOWED_ORIGINS`
- [ ] Setup firewall chi mo port 80/443
- [ ] Setup backup tu dong
- [ ] Giam sat logs thuong xuyen

## Nang cap model AI

### Dung Whisper lon hon

```bash
# Trong .env
WHISPER_MODEL_SIZE=small    # hoac medium, large
WHISPER_COMPUTE_TYPE=float16 # neu co GPU
WHISPER_DEVICE=cuda          # neu co GPU

docker compose up --build -d stt-service
```

### Dung Ollama (thay mock)

```bash
# Cai Ollama tren host
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b

# Trong .env
OLLAMA_BASE_URL=http://host.docker.internal:11434

docker compose restart llm-service
```

### Dung TTS khac (GPT-SoVITS)

```bash
# Trong .env
TTS_PROVIDER_URL=http://your-gptsovits-server:9880

docker compose restart tts-service
```
