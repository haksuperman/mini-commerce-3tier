# Mini Commerce — 3-Tier Deployment (`mini-commerce-3tier`)

🇰🇷 [한국어](#한국어) · 🇬🇧 [English](#english)

`~/mini-commerce-app`(FastAPI + React + MySQL + Redis 모노레포)를 AWS **3계층 아키텍처**로
배포하기 위해 티어별로 분리한 모노레포입니다. 원본은 수정하지 않고 복사 소스로만 사용했습니다.

```
mini-commerce-3tier/
├── web/        # 1계층(Web)  : nginx + React 정적 SPA
├── was/        # 2계층(App)  : FastAPI + Gunicorn/systemd
├── db/         # 3계층(Data) : MySQL 8  (베어메탈/Docker/RDS)
├── cache/      # 3계층(Data) : Redis 7  (베어메탈/Docker/ElastiCache)
├── README.md   # (이 문서) 전체 아키텍처 개요
└── BUILD_LOG.md
```

> "3-tier" = Web / App / Data 3계층 구조. Data 계층을 **db(MySQL)** 와 **cache(Redis)** 두
> 호스트로 물리 분리했기 때문에 폴더는 4개지만 아키텍처는 3계층입니다.
>
> ⚠️ "WAS = Tomcat" 아님 — 원본 백엔드는 **Python FastAPI**(Gunicorn + Uvicorn)입니다.

각 폴더는 독립 배포 단위입니다. 상세 절차는 각 폴더의 `README.md`(한글+영문)를 참고하세요.

---

## 한국어

### 아키텍처 / 티어 간 통신
```
브라우저 ──http──> web(nginx :80) ──/api/ 프록시──> was(Gunicorn :8000) ──> db(MySQL :3306)
                       └ 정적 SPA 서빙 (/var/www/mini-commerce)         └──> cache(Redis :6379)
```
- 브라우저는 **web 티어만** 호출 → 프런트엔드는 `/api/v1` **상대경로** 사용(`VITE_API_BASE_URL=""`),
  nginx 가 WAS 로 프록시하므로 **CORS 불필요**.
- 각 티어는 물리적으로 분리된 호스트에서 구동되며, 통신은 **사설 IP / 관리형 엔드포인트**로 합니다.

| 출발 | 도착 | 설정 위치 | 값 예시 |
|------|------|-----------|---------|
| 브라우저 | web(nginx) | — | `http://<web-domain>` |
| web nginx `/api/` | was | `web/deploy/nginx/*.conf` 의 `__WAS_UPSTREAM__` | `<WAS_사설IP>:8000` |
| was | db(MySQL) | `was` 환경변수 `DATABASE_URL` | `...@<DB_HOST>:3306/minicommerce` |
| was | cache(Redis) | `was` 환경변수 `REDIS_URL` | `redis://<CACHE_HOST>:6379/0` |

**보안그룹**: web `80/443` ← 인터넷 · was `8000` ← web SG 만 · db `3306` ← was SG 만 · cache `6379` ← was SG 만.

### 배포 순서 (권장)
1. **db / cache** 먼저 기동 (데이터 계층).
2. **was**: venv 구성 → `alembic upgrade head`(스키마 생성) → 최초 1회 시드(`RUN_SEED=true`) → systemd 기동.
3. **web**: `VITE_API_BASE_URL=""` 로 빌드 → `/var/www/mini-commerce` 배포 → nginx `__WAS_UPSTREAM__` 치환 후 reload.

폴더별 상세: `web/README.md` · `was/README.md` · `db/README.md` · `cache/README.md`
(관리형: `db/managed/README.md` RDS · `cache/managed/README.md` ElastiCache)

### 티어별 배포 방법

각 티어는 자기 호스트에서 독립적으로 배포합니다. 대상 OS: Amazon Linux 2023 / Ubuntu 22.04+.
(아래는 요약. 각 폴더 `README.md` 에 한글+영문 전체 절차가 있습니다.)

#### web 티어 (nginx + React SPA)
```bash
# 1) 의존성: nginx + Node 20
sudo dnf install -y nginx gettext && curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash - && sudo dnf install -y nodejs   # AL2023
# (Ubuntu: sudo apt-get install -y nginx gettext && curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs)
sudo systemctl enable --now nginx
# 2) 클론 + 설정
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/web
cp deploy/env.example deploy/.env
#   deploy/.env → WAS_UPSTREAM=<WAS 사설IP>:8000 (VITE_API_BASE_URL 은 빈 값 유지=상대경로)
# 3) 빌드 + 배포 (npm ci → 빌드 → /var/www/mini-commerce 복사 → nginx conf 치환 → reload)
sudo -E bash deploy/deploy.sh
# 4) 검증
curl -I http://localhost/ ; curl -s http://localhost/api/v1/products
```

#### was 티어 (FastAPI + Gunicorn/systemd)
```bash
# 1) 의존성: Python 3.12 + 빌드도구
sudo dnf install -y python3.12 python3.12-devel gcc pkg-config mariadb-connector-c-devel rsync   # AL2023
# (Ubuntu: sudo apt-get install -y python3.12 python3.12-venv python3.12-dev gcc pkg-config default-libmysqlclient-dev rsync)
# 2) 클론
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/was
# 3) 환경변수
sudo mkdir -p /etc/mini-commerce && sudo cp deploy/env.example /etc/mini-commerce/was.env && sudo chmod 600 /etc/mini-commerce/was.env
#   was.env → DATABASE_URL(=...@<DB_HOST>:3306/minicommerce), REDIS_URL(=redis://<CACHE_HOST>:6379/0), JWT_SECRET_KEY=$(openssl rand -hex 32)
# 4) 배포 (venv → install → alembic upgrade head → 시드 → systemd 기동)
sudo RUN_SEED=true bash deploy/deploy.sh
# 5) 검증
curl -f http://localhost:8000/healthz/ready    # db·cache reachable 이면 200
```
데모 계정: `admin@minicommerce.local`/`Admin1234!`, `alice@…`/`Alice1234!`, `bob@…`/`Bob1234!`

#### db 티어 (MySQL 8)
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/db
# (A) Docker:
cd docker && MYSQL_ROOT_PASSWORD=ChangeMe_root MYSQL_PASSWORD=ChangeMe_DB_pw docker compose up -d   # 01-init.sql 자동 실행
# (B) 베어메탈:
sudo MYSQL_APP_PASSWORD='ChangeMe_DB_pw' bash baremetal/install-mysql.sh
# (C) 관리형(RDS): managed/README.md 참고
```
프로비저닝 후 WAS 에서 `alembic upgrade head`(테이블 생성), 상품 시드는 선택적으로
`mysql ... < init/02-seed-products.sql`. 3306 은 was SG 에만 개방.

#### cache 티어 (Redis 7)
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/cache
# (A) Docker:
cd docker && docker compose up -d && docker compose exec redis redis-cli ping   # → PONG
# (B) 베어메탈:
sudo bash baremetal/install-redis.sh && redis-cli ping
# (C) 관리형(ElastiCache): managed/README.md 참고
```
6379 는 was SG 에만 개방. WAS 의 `REDIS_URL=redis://<이 호스트>:6379/0` 으로 참조.

### 한 번에 따라하기 — 4서버 배포 예시 (사설 IP 예시)

EC2 4대를 가정. 아래 예시 값만 본인 환경으로 바꾸면 됩니다.

| 호스트 | 역할 | 예시 사설 IP | 비고 |
|--------|------|--------------|------|
| db | MySQL 8 | `10.0.3.10` | 인터넷 비공개 |
| cache | Redis 7 | `10.0.3.20` | 인터넷 비공개 |
| was | FastAPI | `10.0.2.10` | 인터넷 비공개 |
| web | nginx | `10.0.1.10` | 공인 IP/도메인 부여 |

예시 DB 비밀번호: `ChangeMe_DB_pw`  ·  예시 JWT 시크릿: `openssl rand -hex 32` 결과값

**① db 호스트 (10.0.3.10)** — Docker 예시
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/db/docker
MYSQL_ROOT_PASSWORD=ChangeMe_root MYSQL_PASSWORD=ChangeMe_DB_pw docker compose up -d
# (베어메탈은 db/README.md 의 install-mysql.sh 참고)
```

**② cache 호스트 (10.0.3.20)** — Docker 예시
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/cache/docker
docker compose up -d
docker compose exec redis redis-cli ping   # → PONG
```

**③ was 호스트 (10.0.2.10)**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/was
sudo mkdir -p /etc/mini-commerce && sudo cp deploy/env.example /etc/mini-commerce/was.env
sudo sed -i \
  -e 's#<password>#ChangeMe_DB_pw#; s#<DB_HOST>#10.0.3.10#; s#<CACHE_HOST>#10.0.3.20#' \
  -e "s#<production-secret>#$(openssl rand -hex 32)#" \
  -e 's#<web-tier-domain>#10.0.1.10#' /etc/mini-commerce/was.env
# 의존성(예: Amazon Linux 2023): python3.12 등 — was/README.md 1) 참고
sudo RUN_SEED=true bash deploy/deploy.sh
curl -f http://localhost:8000/healthz/ready    # db·cache 모두 reachable 이면 200
```

**④ web 호스트 (10.0.1.10)**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/web
cp deploy/env.example deploy/.env
sed -i 's#^WAS_UPSTREAM=.*#WAS_UPSTREAM=10.0.2.10:8000#' deploy/.env   # VITE_API_BASE_URL 은 빈 값 유지
# 의존성(nginx·Node20) 설치는 web/README.md 1) 참고
sudo -E bash deploy/deploy.sh
```

**⑤ 동작 확인** — 브라우저로 `http://10.0.1.10/` 접속 → 상품 목록 로드(상대경로 `/api/v1/products`,
CORS 에러 없음) → 데모 계정(`admin@minicommerce.local` / `Admin1234!`)으로 로그인 → 장바구니(Redis) →
주문(MySQL) 플로우가 web→was→db/cache 로 동작.

> 보안그룹은 위 표대로: web(80/443)←인터넷, was(8000)←web SG, db(3306)←was SG, cache(6379)←was SG.
> 관리형(RDS/ElastiCache)을 쓰면 ①②를 건너뛰고 엔드포인트를 ③의 `DATABASE_URL`/`REDIS_URL` 에 넣으면 됩니다.

### 스키마 · 시드 소유권
- **스키마(테이블)** 는 **was** 가 Alembic(`was/alembic/`)으로 소유. db 티어는 서버·DB·유저·권한만 프로비저닝.
- **유저 시드**(bcrypt)는 was `deploy/seed.py` 가 담당. **상품 시드**는 was `seed.py` 또는 db `init/02-seed-products.sql`(마이그레이션 후) 양쪽 제공.

### 원본
`~/mini-commerce-app`(frontend / backend / docker-compose.yml / scripts)에서 추출, 원본·git 히스토리 무손상.

---

## English

3-tier monorepo that splits `~/mini-commerce-app` (a FastAPI + React + MySQL + Redis
monorepo) into deployment tiers for an AWS **3-tier architecture**. The original is
used only as a copy source and is left untouched.

> "3-tier" = Web / App / Data. The Data tier is physically split into **db (MySQL)**
> and **cache (Redis)** hosts, so there are 4 folders but 3 architectural tiers.
>
> ⚠️ "WAS ≠ Tomcat" — the backend is **Python FastAPI** (Gunicorn + Uvicorn).

### Architecture / inter-tier communication
```
browser ──http──> web (nginx :80) ──/api/ proxy──> was (Gunicorn :8000) ──> db (MySQL :3306)
                       └── serves static SPA from /var/www/mini-commerce  └──> cache (Redis :6379)
```
- The browser only ever talks to the **web** tier → the SPA uses **relative**
  `/api/v1` paths (`VITE_API_BASE_URL=""`) and nginx reverse-proxies to WAS, so
  **no CORS** is needed.
- Each tier runs on a separate host; communication uses **private IPs / managed
  endpoints**.

| From | To | Config location | Example |
|------|------|-----------------|---------|
| browser | web (nginx) | — | `http://<web-domain>` |
| web nginx `/api/` | was | `__WAS_UPSTREAM__` in `web/deploy/nginx/*.conf` | `<WAS_PRIVATE_IP>:8000` |
| was | db (MySQL) | `DATABASE_URL` (was env) | `...@<DB_HOST>:3306/minicommerce` |
| was | cache (Redis) | `REDIS_URL` (was env) | `redis://<CACHE_HOST>:6379/0` |

**Security groups**: web `80/443` ← internet · was `8000` ← web SG · db `3306` ← was SG · cache `6379` ← was SG.

### Recommended deploy order
1. **db / cache** first (data tier).
2. **was**: build venv → `alembic upgrade head` (schema) → seed once (`RUN_SEED=true`) → start systemd.
3. **web**: build with `VITE_API_BASE_URL=""` → publish to `/var/www/mini-commerce` → substitute `__WAS_UPSTREAM__` and reload nginx.

Per-folder details: `web/README.md` · `was/README.md` · `db/README.md` · `cache/README.md`
(managed: `db/managed/README.md` for RDS · `cache/managed/README.md` for ElastiCache).

### Per-tier deployment

Each tier deploys independently on its own host. Target OS: Amazon Linux 2023 /
Ubuntu 22.04+. (Summary below; each folder's `README.md` has the full KO+EN steps.)

#### web tier (nginx + React SPA)
```bash
# 1) deps: nginx + Node 20
sudo dnf install -y nginx gettext && curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash - && sudo dnf install -y nodejs   # AL2023
# (Ubuntu: sudo apt-get install -y nginx gettext && curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs)
sudo systemctl enable --now nginx
# 2) clone + configure
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/web
cp deploy/env.example deploy/.env
#   deploy/.env → WAS_UPSTREAM=<WAS private IP>:8000 (keep VITE_API_BASE_URL empty = relative paths)
# 3) build + deploy (npm ci → build → copy to /var/www/mini-commerce → render nginx conf → reload)
sudo -E bash deploy/deploy.sh
# 4) verify
curl -I http://localhost/ ; curl -s http://localhost/api/v1/products
```

#### was tier (FastAPI + Gunicorn/systemd)
```bash
# 1) deps: Python 3.12 + build tools
sudo dnf install -y python3.12 python3.12-devel gcc pkg-config mariadb-connector-c-devel rsync   # AL2023
# (Ubuntu: sudo apt-get install -y python3.12 python3.12-venv python3.12-dev gcc pkg-config default-libmysqlclient-dev rsync)
# 2) clone
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/was
# 3) environment
sudo mkdir -p /etc/mini-commerce && sudo cp deploy/env.example /etc/mini-commerce/was.env && sudo chmod 600 /etc/mini-commerce/was.env
#   was.env → DATABASE_URL(=...@<DB_HOST>:3306/minicommerce), REDIS_URL(=redis://<CACHE_HOST>:6379/0), JWT_SECRET_KEY=$(openssl rand -hex 32)
# 4) deploy (venv → install → alembic upgrade head → seed → start systemd)
sudo RUN_SEED=true bash deploy/deploy.sh
# 5) verify
curl -f http://localhost:8000/healthz/ready    # 200 when db & cache are reachable
```
Demo accounts: `admin@minicommerce.local`/`Admin1234!`, `alice@…`/`Alice1234!`, `bob@…`/`Bob1234!`

#### db tier (MySQL 8)
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/db
# (A) Docker:
cd docker && MYSQL_ROOT_PASSWORD=ChangeMe_root MYSQL_PASSWORD=ChangeMe_DB_pw docker compose up -d   # 01-init.sql runs automatically
# (B) bare metal:
sudo MYSQL_APP_PASSWORD='ChangeMe_DB_pw' bash baremetal/install-mysql.sh
# (C) managed (RDS): see managed/README.md
```
After provisioning, run `alembic upgrade head` from WAS (creates tables); product seed is
optional via `mysql ... < init/02-seed-products.sql`. Open 3306 to the was SG only.

#### cache tier (Redis 7)
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/cache
# (A) Docker:
cd docker && docker compose up -d && docker compose exec redis redis-cli ping   # → PONG
# (B) bare metal:
sudo bash baremetal/install-redis.sh && redis-cli ping
# (C) managed (ElastiCache): see managed/README.md
```
Open 6379 to the was SG only. WAS references it via `REDIS_URL=redis://<this-host>:6379/0`.

### End-to-end walkthrough — 4-server example (sample private IPs)

Assuming 4 EC2 hosts. Replace the example values with your own.

| Host | Role | Sample private IP | Note |
|------|------|-------------------|------|
| db | MySQL 8 | `10.0.3.10` | not internet-facing |
| cache | Redis 7 | `10.0.3.20` | not internet-facing |
| was | FastAPI | `10.0.2.10` | not internet-facing |
| web | nginx | `10.0.1.10` | public IP/domain |

Sample DB password: `ChangeMe_DB_pw` · Sample JWT secret: output of `openssl rand -hex 32`

**① db host (10.0.3.10)** — Docker example
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/db/docker
MYSQL_ROOT_PASSWORD=ChangeMe_root MYSQL_PASSWORD=ChangeMe_DB_pw docker compose up -d
# (bare metal: see install-mysql.sh in db/README.md)
```

**② cache host (10.0.3.20)** — Docker example
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/cache/docker
docker compose up -d
docker compose exec redis redis-cli ping   # → PONG
```

**③ was host (10.0.2.10)**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/was
sudo mkdir -p /etc/mini-commerce && sudo cp deploy/env.example /etc/mini-commerce/was.env
sudo sed -i \
  -e 's#<password>#ChangeMe_DB_pw#; s#<DB_HOST>#10.0.3.10#; s#<CACHE_HOST>#10.0.3.20#' \
  -e "s#<production-secret>#$(openssl rand -hex 32)#" \
  -e 's#<web-tier-domain>#10.0.1.10#' /etc/mini-commerce/was.env
# deps (e.g. Amazon Linux 2023): python3.12 etc. — see was/README.md step 1
sudo RUN_SEED=true bash deploy/deploy.sh
curl -f http://localhost:8000/healthz/ready    # 200 when both db & cache are reachable
```

**④ web host (10.0.1.10)**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/web
cp deploy/env.example deploy/.env
sed -i 's#^WAS_UPSTREAM=.*#WAS_UPSTREAM=10.0.2.10:8000#' deploy/.env   # keep VITE_API_BASE_URL empty
# install deps (nginx, Node 20) — see web/README.md step 1
sudo -E bash deploy/deploy.sh
```

**⑤ Smoke test** — open `http://10.0.1.10/` in a browser → product list loads (relative
`/api/v1/products`, no CORS error) → log in with a demo account
(`admin@minicommerce.local` / `Admin1234!`) → cart (Redis) → order (MySQL) flows through
web→was→db/cache.

> Security groups as in the table above: web(80/443)←internet, was(8000)←web SG,
> db(3306)←was SG, cache(6379)←was SG. With managed RDS/ElastiCache, skip ①② and put
> their endpoints into step ③'s `DATABASE_URL`/`REDIS_URL`.

### Schema & seed ownership
- The **schema (tables)** is owned by **was** via Alembic (`was/alembic/`); the db tier only provisions server/DB/user/grants.
- **User seeding** (bcrypt) is done by was `deploy/seed.py`. **Product seeding** is available via was `seed.py` or db `init/02-seed-products.sql` (after migrations).

### Source
Extracted from `~/mini-commerce-app` (frontend / backend / docker-compose.yml / scripts); the original and its git history are untouched.
