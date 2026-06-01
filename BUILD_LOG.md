# Mini Commerce 멀티 티어 추출 — BUILD LOG

자율 모드 실행 기록. 원본 `~/mini-commerce-app` 은 READ-ONLY(복사 소스). 모든 쓰기는 `~/mini-commerce-tiers/` 하위에서만 수행.

- 작업일: 2026-05-31 (KST)
- 권위 설계 문서: `/Users/haksu/.claude/plans/delegated-discovering-robin.md`
- 결과: **4개 티어(web/was/db/cache) 독립 git 레포 생성 + 검증 완료. 원본 무손상.**

---

## 1. 원본 무손상 — git status 스냅샷

`cd ~/mini-commerce-app && git status --porcelain`

| 시점 | 결과 |
|------|------|
| 시작 | ` D .claude/scheduled_tasks.lock` |
| 종료 | ` D .claude/scheduled_tasks.lock` |

- 시작=종료 동일. 신규 변경 **없음**. (`D .claude/scheduled_tasks.lock` 은 원래부터 있던 한 줄 → 무시 대상)
- 원본 HEAD: `b52bbd3` (시작·종료 동일, 변동 없음).
- ✅ 원본 및 `.git` 완전 무손상.

---

## 2. 완료 체크리스트

- [x] 0. 디렉터리 생성 + rsync(web/was) + BUILD_LOG 초기화
- [x] 1. web 티어 산출물 생성 + git commit
- [x] 2. was 티어 산출물 생성 + git commit
- [x] 3. db 티어 산출물 생성 + git commit
- [x] 4. cache 티어 산출물 생성 + git commit
- [x] 5. 정적 검증 (핵심 파일 존재 + 각 레포 1커밋)
- [x] 6. best-effort 빌드/import 검증 (web 빌드, was import, compose config)
- [x] 7. 원본 무손상 재확인 + 최종 보고

---

## 3. 각 레포 경로 / 커밋

| 티어 | 경로 | 커밋 해시 | 커밋 수 |
|------|------|-----------|---------|
| web | `~/mini-commerce-tiers/web` | `deec0f08cc1b3db0d25eeff837788c3334cea244` | 1 |
| was | `~/mini-commerce-tiers/was` | `3fc7158302fdda0864f8503d937daa5c53abca44` | 1 |
| db | `~/mini-commerce-tiers/db` | `14e3419591c0d04706706109fa566cde06e4f129` | 1 |
| cache | `~/mini-commerce-tiers/cache` | `ef2d8e53b7baac1e31b74d59f9563bd502168039` | 1 |

커밋 메시지: `Initial <tier> tier extraction from mini-commerce-app` (author: Haksu Park <tky6012@gmail.com>)

> 후속 변경(2026-06-01): 각 티어 `README.md` 를 **한글+영문 이중 언어**로 갱신하고 초기 커밋을
> amend(레포당 1커밋 유지). 위 해시는 amend 후 최신값. 최상위 `~/mini-commerce-tiers/README.md`
> 는 불필요하여 생성 후 삭제(각 레포를 따로 push 하므로). 원본은 여전히 무손상.

### 산출물 구조 요약
```
web/    app/(frontend 복사) + deploy/nginx/mini-commerce-web.conf + deploy.sh + env.example + README + .gitignore
was/    app/ alembic/ pyproject.toml (backend 복사) + deploy/{systemd/*.service, gunicorn.conf.py, deploy.sh, seed.py, env.example} + README + .gitignore
db/     baremetal/{install-mysql.sh, my.cnf} + docker/docker-compose.yml + init/{01-init.sql, 02-seed-products.sql} + managed/README.md + README + .gitignore
cache/  baremetal/{install-redis.sh, redis.conf} + docker/docker-compose.yml + managed/README.md + README + .gitignore
```

---

## 4. 검증 결과

### 정적 검증 (필수) — 전부 PASS
- 각 레포 핵심 파일 존재: web(package.json·src·nginx conf·deploy.sh), was(app·alembic·pyproject·systemd·gunicorn.conf.py), db(compose·01-init.sql·my.cnf), cache(compose·redis.conf) ✅
- 각 레포 git log 정확히 1커밋 ✅

### best-effort 동적 검증
| 항목 | 결과 | 비고 |
|------|------|------|
| web `VITE_API_BASE_URL="" npm ci && npm run build` | ✅ PASS | dist 생성, vite 5.4.21, 빌드 602ms |
| web 번들 상대경로 확인 | ✅ PASS | 번들에 `localhost:8000` 없음, `/api/v1` 상대경로 baked → CORS 불필요 구조 확인 |
| was venv + `pip install .` | ✅ PASS | python3.12, fastapi/gunicorn/uvicorn/asyncmy/alembic/redis 등 설치, `pip check` 무결 |
| was `python -c "import app.main"` | ✅ PASS | `IMPORT OK: app.main loaded` |
| was `deploy/seed.py` 임포트 | ✅ PASS | app.models/app.security 해석, SEED_PRODUCTS=20 / users=3 |
| was `gunicorn.conf.py` 구문 | ✅ PASS | ast 파싱 OK |
| db/cache `docker compose config` | ✅ PASS | 두 compose 모두 문법 VALID (데몬 불필요한 정적 파싱) |

### was 가동 인자 일치 확인
`deploy/systemd/mini-commerce-was.service` 및 `deploy/gunicorn.conf.py` 는 원본 `backend/Dockerfile` CMD 와 동일:
UvicornWorker · bind 0.0.0.0:8000 · workers 2 · timeout 60 · graceful-timeout 30 · keep-alive 5 · access/error log → stdout.

---

## 5. 건너뛴 항목 / 사유

| 항목 | 사유 |
|------|------|
| `nginx -t` 문법 검증 | 로컬에 nginx 미설치(`which nginx` → none). conf 는 정적 작성, deploy.sh 가 EC2에서 `nginx -t` 수행하도록 구성. |
| Docker 풀 E2E (web→was→db/cache) | colima 데몬 미실행(`/Users/haksu/.colima/default/docker.sock` 없음). 시스템 변경/기동 회피 위해 데몬 미기동. compose 파일은 `docker compose config` 로 문법 검증 완료. 원본 compose 는 절대 미사용. |
| db/cache 컨테이너 단독 스모크(redis-cli ping / MySQL init) | 위와 동일(데몬 미실행). compose 는 원본 redis/mysql 서비스에서 1:1 추출 + config 검증으로 대체. |

---

## 6. 결정 사항 로그 (합리적 기본값)

1. **rsync 추가 제외**: 계획서 exclude 외 `.coverage`, `htmlcov`(was) 도 제외 — 테스트 산출물, 배포 불필요.
2. **db `02-seed-products.sql` 자동실행 제외**: `products` 테이블은 WAS Alembic 이 생성하므로 MySQL 최초 부팅(initdb) 시점엔 테이블이 없음. 자동 마운트 시 INSERT 실패로 initdb 가 깨짐. → docker-compose 는 `01-init.sql` 만 initdb 로 마운트하고, `02-seed-products.sql` 은 "마이그레이션 후 수동 실행"용으로 헤더에 명시. 각 INSERT 는 `WHERE NOT EXISTS(name)` 로 멱등.
3. **was 의 seed**: 원본 `scripts/seed.py` 는 `../backend` 경로를 sys.path 에 넣지만 was 레포는 `app/` 가 루트라, `deploy/seed.py` 로 복제하며 경로를 레포 루트(=deploy 의 부모)로 조정. 유저 시드(bcrypt)는 WAS 담당, 상품 시드는 SQL/seed.py 양쪽 제공.
4. **was deploy.sh 의존성 설치**: poetry 있으면 `poetry install --only=main`, 없으면 `pip install .` 로 폴백(검증은 pip 경로로 통과 확인).
5. **redis.conf 네트워크**: 티어 분리(별도 호스트) 전제 → `bind 0.0.0.0` + `protected-mode no` 기본값, 단 "보안그룹으로 6379 를 WAS SG 로만 제한" 을 주석/README 에 강하게 명시. requirepass 옵션도 주석 제공.
6. **web nginx**: 원본 `frontend/nginx.conf`(8080, 프록시 없음)는 `app/` 안에 그대로 보존(Docker 단독용). 멀티티어용 리버스 프록시 conf 는 `deploy/nginx/mini-commerce-web.conf`(80 listen, `/api/` → `__WAS_UPSTREAM__`) 로 신규 작성. deploy.sh 가 `sed` 로 `__WAS_UPSTREAM__` 치환(envsubst 대신 sed 사용 — nginx `$` 변수 보존 위해).

---

## 7. 아침에 사람이 이어서 할 일 (원격 연결 — 본 작업 범위 밖, 미수행)

본 작업은 **로컬 git init + commit 까지만** 수행했다(원격/push 금지 제약). 다음을 수동 진행:

1. GitHub(또는 사내 git)에 빈 레포 4개 생성: `mini-commerce-web`, `mini-commerce-was`, `mini-commerce-db`, `mini-commerce-cache`.
2. 각 티어 디렉터리에서 remote 연결 후 push:
   ```bash
   cd ~/mini-commerce-tiers/web   && git remote add origin <web-repo-url>   && git push -u origin main
   cd ~/mini-commerce-tiers/was   && git remote add origin <was-repo-url>   && git push -u origin main
   cd ~/mini-commerce-tiers/db    && git remote add origin <db-repo-url>    && git push -u origin main
   cd ~/mini-commerce-tiers/cache && git remote add origin <cache-repo-url> && git push -u origin main
   ```
   (현재 브랜치명이 `master` 면 `git branch -M main` 후 push)
3. EC2 4대(또는 RDS/ElastiCache) 프로비저닝 후 각 README 의 배포 절차 수행. 통신 설정값:
   - web `deploy/.env` → `WAS_UPSTREAM=<WAS 사설IP>:8000`
   - was `/etc/mini-commerce/was.env` → `DATABASE_URL=...@<DB_HOST>:3306/minicommerce`, `REDIS_URL=redis://<CACHE_HOST>:6379/0`, `JWT_SECRET_KEY=$(openssl rand -hex 32)`
   - 보안그룹: web(80/443)←인터넷, was(8000)←web SG, db(3306)←was SG, cache(6379)←was SG.
4. 배포 순서 권장: db·cache 먼저 → was(`alembic upgrade head`, RUN_SEED=true 1회) → web(빌드+배포).
5. (선택) 로컬 검증으로 생긴 `web/app/node_modules`, `web/app/dist`, `was/.venv` 는 .gitignore 처리되어 커밋 안 됨. 정리하려면 삭제 가능(필수 아님).

---

## 8. 최종 확인

- ✅ 원본 `~/mini-commerce-app` 무손상 (git status 시작=종료, HEAD 불변).
- ✅ 4개 티어 레포 각 1커밋 + 핵심 파일 검증.
- ✅ web 빌드 / was import / compose config 동적 검증 통과.
- ⏭️ nginx -t · Docker 풀 E2E 는 환경 제약으로 건너뜀(사유 위 5절).
