# Mini Commerce — 3-Tier Deployment (`mini-commerce-3tier`)

🇰🇷 [한국어](#한국어) · 🇬🇧 [English](#english)

**Mini Commerce** — FastAPI + React + MySQL + Redis 로 만든 커머스 데모 앱을, AWS **3계층
아키텍처**(web / was / data)로 배포하도록 티어별로 구성한 모노레포입니다.

```
mini-commerce-3tier/
├── web/        # 1계층(Web)  : nginx + React 정적 SPA
├── was/        # 2계층(App)  : FastAPI + Gunicorn/systemd
├── db/         # 3계층(Data) : MySQL 8  (베어메탈/Docker/RDS)
├── cache/      # 3계층(Data) : Redis 7  (베어메탈/Docker/ElastiCache)
└── README.md   # (이 문서) 전체 아키텍처 개요
```

> "3-tier" = Web / App / Data 3계층 구조. Data 계층을 **db(MySQL)** 와 **cache(Redis)** 두
> 호스트로 물리 분리했기 때문에 폴더는 4개지만 아키텍처는 3계층입니다.
>
> ⚠️ "WAS = Tomcat" 아님 — 백엔드는 **Python FastAPI**(Gunicorn + Uvicorn)입니다.

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

### 📦 티어별 배포 방법 — 각 폴더의 README 를 보세요

**각 티어의 상세 배포 절차(의존성 설치 → 클론 → 설정 → 배포 → 검증)는 그 티어 폴더의 `README.md` 에 한글+영문으로 들어 있습니다.** 배포할 서버에서 해당 폴더의 README 를 열어 그대로 따라가면 됩니다.

| 티어 | 배포 문서 | 비고 |
|------|-----------|------|
| web (nginx) | **[`web/README.md`](web/README.md)** | 정적 SPA + `/api` 리버스 프록시 |
| was (FastAPI) | **[`was/README.md`](was/README.md)** | Gunicorn/systemd, 스키마·시드 소유 |
| db (MySQL) | **[`db/README.md`](db/README.md)** | 설치형 / 관리형 [RDS](db/managed/README.md) |
| cache (Redis) | **[`cache/README.md`](cache/README.md)** | 설치형 / 관리형 [ElastiCache](cache/managed/README.md) |

> 여러 호스트를 실제 IP로 한 번에 연결하는 통합 예시는 아래 "한 번에 따라하기" 를 참고하세요.

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
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/db/docker
MYSQL_ROOT_PASSWORD=ChangeMe_root MYSQL_PASSWORD=ChangeMe_DB_pw docker compose up -d
# (베어메탈은 db/README.md 의 install-mysql.sh 참고)
```

**② cache 호스트 (10.0.3.20)** — Docker 예시
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/cache/docker
docker compose up -d
docker compose exec redis redis-cli ping   # → PONG
```

**③ was 호스트 (10.0.2.10)**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/was
sudo mkdir -p /etc/mini-commerce
sudo cp deploy/env.example /etc/mini-commerce/was.env
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
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/web
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

---

## English

**Mini Commerce** — a commerce demo app (FastAPI + React + MySQL + Redis), structured as
a monorepo for deployment on an AWS **3-tier architecture** (web / was / data).

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

### 📦 Per-tier deployment — see each folder's README

**The full deploy steps for each tier (install deps → clone → configure → deploy → verify) live in that tier's folder `README.md` (KO + EN).** On the server you're deploying, open that folder's README and follow it.

| Tier | Deploy doc | Notes |
|------|-----------|-------|
| web (nginx) | **[`web/README.md`](web/README.md)** | static SPA + `/api` reverse proxy |
| was (FastAPI) | **[`was/README.md`](was/README.md)** | Gunicorn/systemd, owns schema/seed |
| db (MySQL) | **[`db/README.md`](db/README.md)** | self-managed / managed [RDS](db/managed/README.md) |
| cache (Redis) | **[`cache/README.md`](cache/README.md)** | self-managed / managed [ElastiCache](cache/managed/README.md) |

> To wire several hosts together with real IPs at once, see the end-to-end walkthrough below.

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
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/db/docker
MYSQL_ROOT_PASSWORD=ChangeMe_root MYSQL_PASSWORD=ChangeMe_DB_pw docker compose up -d
# (bare metal: see install-mysql.sh in db/README.md)
```

**② cache host (10.0.3.20)** — Docker example
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/cache/docker
docker compose up -d
docker compose exec redis redis-cli ping   # → PONG
```

**③ was host (10.0.2.10)**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/was
sudo mkdir -p /etc/mini-commerce
sudo cp deploy/env.example /etc/mini-commerce/was.env
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
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/web
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
