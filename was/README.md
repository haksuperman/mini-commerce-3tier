# Mini Commerce — WAS Tier (FastAPI + Gunicorn)

🇰🇷 [한국어](#한국어) · 🇬🇧 [English](#english)

---

## 한국어

Mini Commerce 멀티 티어 배포의 **애플리케이션 티어(WAS)** 입니다. FastAPI 백엔드를 Gunicorn
(Uvicorn 워커)으로 systemd 서비스로 구동합니다. DB **스키마**(Alembic)와 **시드** 데이터를 소유하고,
**db 티어**(MySQL)·**cache 티어**(Redis)로 연결하며, **web 티어**의 nginx 리버스 프록시로만
접근됩니다.

> ⚠️ 이것은 **Python FastAPI** 이며 Java/Tomcat 이 아닙니다. WAS 호스트에는 서블릿 컨테이너가
> 아니라 **Python 3.12 + Gunicorn** 이 설치됩니다.

```
was/
├── app/ alembic/ alembic.ini        # FastAPI 앱 (backend 복사본)
├── pyproject.toml poetry.lock tests/
├── Dockerfile                        # 원본 backend Dockerfile (선택)
├── deploy/
│   ├── systemd/mini-commerce-was.service
│   ├── gunicorn.conf.py              # bind 0.0.0.0:8000, UvicornWorker, workers=2
│   ├── deploy.sh                     # venv → 설치 → 마이그레이션 → (시드) → systemd
│   ├── seed.py                       # 멱등 데모 시드 (유저 + 상품)
│   └── env.example                   # 운영 환경변수 (DATABASE_URL, REDIS_URL, ...)
├── README.md
└── .gitignore
```

### 아키텍처
```
web nginx ──/api/ 프록시──> was(Gunicorn :8000) ──> db(MySQL :3306)
                                              └──> cache(Redis :6379)
```
보안그룹: was `8000` ← web SG 만 · db `3306` ← was SG · cache `6379` ← was SG.

### EC2 / 베어메탈 배포

대상: Amazon Linux 2023 / Ubuntu 22.04+

**1) Python 3.12 + 빌드 의존성 설치**

Amazon Linux 2023:
```bash
sudo dnf install -y python3.12 python3.12-devel gcc pkg-config \
    mariadb-connector-c-devel rsync
```
Ubuntu 22.04+ (3.12 필요 시 deadsnakes):
```bash
sudo apt-get update && sudo apt-get install -y \
    python3.12 python3.12-venv python3.12-dev gcc pkg-config \
    default-libmysqlclient-dev rsync
```

**2) 환경변수 설정**
```bash
sudo mkdir -p /etc/mini-commerce
sudo cp deploy/env.example /etc/mini-commerce/was.env
sudo chmod 600 /etc/mini-commerce/was.env
# /etc/mini-commerce/was.env 편집:
#   DATABASE_URL=mysql+asyncmy://minicommerce:<pw>@<DB_HOST>:3306/minicommerce
#   REDIS_URL=redis://<CACHE_HOST>:6379/0
#   JWT_SECRET_KEY=$(openssl rand -hex 32)
```

**3) 배포**
```bash
git clone <was-repo-url> mini-commerce-was && cd mini-commerce-was
# 최초 배포: 데모 데이터 시드 포함
sudo RUN_SEED=true bash deploy/deploy.sh
```
`deploy.sh` 는 소스를 `/opt/mini-commerce-was` 로 동기화하고, venv 생성·앱 설치,
`alembic upgrade head` 실행, 선택적 시드, systemd 유닛 설치 후 `mini-commerce-was` 를 기동합니다.

**4) 검증**
```bash
systemctl status mini-commerce-was
curl -f http://localhost:8000/healthz/ready   # DB + Redis 가 reachable 일 때만 200
curl -s http://localhost:8000/docs            # OpenAPI UI
```
`/healthz/ready` 는 db·cache 티어가 모두 reachable 할 때만 200 을 반환하므로 데이터 티어
연결성 점검을 겸합니다.

### 마이그레이션 · 시드 소유권
앱이 스키마의 source of truth 입니다. 마이그레이션은 `alembic/` 에 있고 `deploy.sh` 에서
실행됩니다(`RUN_MIGRATIONS_ON_START=false` 로 부팅 시 워커 경합 방지). 데모 유저는 bcrypt
해시가 필요하므로 유저 시드는 db 티어 SQL 이 아니라 여기 Python(`deploy/seed.py`)에서 합니다.

### Docker (선택)
원본 `Dockerfile` 이 동일한 Gunicorn 이미지(`:8000`)를 빌드합니다. db·cache 티어 호스트를 가리키는
`DATABASE_URL` / `REDIS_URL` 을 주입하세요.

### 원본
`mini-commerce-app/backend` 에서 추출했으며 원본은 수정하지 않았습니다.

---

## English

The **application tier** of the Mini Commerce multi-tier deployment. Runs the
FastAPI backend under Gunicorn (Uvicorn workers) as a systemd service. It owns the
database **schema** (Alembic) and **seed** data, connects out to the **db** tier
(MySQL) and **cache** tier (Redis), and is reached only by the **web** tier's
nginx reverse proxy.

> ⚠️ This is **Python FastAPI**, not Java/Tomcat. The "WAS" host runs
> Python 3.12 + Gunicorn, not a servlet container.

```
was/
├── app/ alembic/ alembic.ini        # FastAPI app (copy of backend/)
├── pyproject.toml poetry.lock tests/
├── Dockerfile                        # original backend Dockerfile (optional)
├── deploy/
│   ├── systemd/mini-commerce-was.service
│   ├── gunicorn.conf.py              # bind 0.0.0.0:8000, UvicornWorker, workers=2
│   ├── deploy.sh                     # venv → install → migrate → (seed) → systemd
│   ├── seed.py                       # idempotent demo seed (users + products)
│   └── env.example                   # production env (DATABASE_URL, REDIS_URL, ...)
├── README.md
└── .gitignore
```

### Architecture
```
web nginx ──/api/ proxy──> was (Gunicorn :8000) ──> db (MySQL :3306)
                                                └──> cache (Redis :6379)
```
Security group: was `8000` ← web SG only · db `3306` ← was SG · cache `6379` ← was SG.

### EC2 / bare-metal deploy

Tested target: Amazon Linux 2023 / Ubuntu 22.04+.

**1) Install Python 3.12 + build deps**

Amazon Linux 2023:
```bash
sudo dnf install -y python3.12 python3.12-devel gcc pkg-config \
    mariadb-connector-c-devel rsync
```
Ubuntu 22.04+ (deadsnakes for 3.12 if needed):
```bash
sudo apt-get update && sudo apt-get install -y \
    python3.12 python3.12-venv python3.12-dev gcc pkg-config \
    default-libmysqlclient-dev rsync
```

**2) Configure environment**
```bash
sudo mkdir -p /etc/mini-commerce
sudo cp deploy/env.example /etc/mini-commerce/was.env
sudo chmod 600 /etc/mini-commerce/was.env
# edit /etc/mini-commerce/was.env:
#   DATABASE_URL=mysql+asyncmy://minicommerce:<pw>@<DB_HOST>:3306/minicommerce
#   REDIS_URL=redis://<CACHE_HOST>:6379/0
#   JWT_SECRET_KEY=$(openssl rand -hex 32)
```

**3) Deploy**
```bash
git clone <was-repo-url> mini-commerce-was && cd mini-commerce-was
# first deploy: also seed demo data
sudo RUN_SEED=true bash deploy/deploy.sh
```
`deploy.sh` syncs the source to `/opt/mini-commerce-was`, builds a venv, installs
the app, runs `alembic upgrade head`, optionally seeds, installs the systemd unit
and starts `mini-commerce-was`.

**4) Verify**
```bash
systemctl status mini-commerce-was
curl -f http://localhost:8000/healthz/ready   # 200 only if DB + Redis reachable
curl -s http://localhost:8000/docs            # OpenAPI UI
```
`/healthz/ready` returns 200 only when both the db and cache tiers are reachable,
so it doubles as a connectivity check for the data tiers.

### Migrations & seed ownership
The app is the schema source of truth. Migrations live in `alembic/` and run from
`deploy.sh` (`RUN_MIGRATIONS_ON_START=false` so workers don't race on boot).
Demo users are bcrypt-hashed, so user seeding is done here in Python
(`deploy/seed.py`), not in the db tier's SQL.

### Docker (optional)
The original `Dockerfile` builds the same Gunicorn image (`:8000`). Provide
`DATABASE_URL` / `REDIS_URL` pointing at the db and cache tier hosts.

### Source
Extracted from `mini-commerce-app/backend` without modifying the original.
