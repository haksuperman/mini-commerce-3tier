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

### Schema & seed ownership
- The **schema (tables)** is owned by **was** via Alembic (`was/alembic/`); the db tier only provisions server/DB/user/grants.
- **User seeding** (bcrypt) is done by was `deploy/seed.py`. **Product seeding** is available via was `seed.py` or db `init/02-seed-products.sql` (after migrations).

### Source
Extracted from `~/mini-commerce-app` (frontend / backend / docker-compose.yml / scripts); the original and its git history are untouched.
