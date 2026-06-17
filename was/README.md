# Mini Commerce — WAS Tier (FastAPI + Gunicorn)

Mini Commerce 멀티 티어 배포의 **애플리케이션 티어(WAS)** 입니다. FastAPI 백엔드를 Gunicorn
(Uvicorn 워커)으로 systemd 서비스로 구동합니다. DB **스키마**(Alembic)와 **시드** 데이터를 소유하고,
**db 티어**(MySQL)·**cache 티어**(Redis)로 연결하며, **web 티어**의 nginx 리버스 프록시로만
접근됩니다.

> ⚠️ 이것은 **Python FastAPI** 이며 Java/Tomcat 이 아닙니다. WAS 호스트에는 서블릿 컨테이너가
> 아니라 **Python 3.12 + Gunicorn** 이 설치됩니다.

```
was/
├── app/ alembic/ alembic.ini        # FastAPI 앱
├── pyproject.toml poetry.lock tests/
├── Dockerfile                        # backend Dockerfile (선택)
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

> ⛔ **WAS는 db·cache 가 먼저 떠 있어야 부팅됩니다.** 기동 시 lifespan(`app/main.py`)이 DB 커넥션 풀을
> warm-up 하고 `redis.ping()` 으로 캐시를 점검하는데, **둘 중 하나라도 닿지 않으면** 워커가 부팅에 실패하고
> (`journalctl` 에 `redis.exceptions.TimeoutError` / `Worker failed to boot`) systemd 가 크래시 루프에
> 빠집니다. web 에서는 502/504 로 보입니다. → **반드시 [db](../db/README.md)·[cache](../cache/README.md) 를
> 먼저 기동하고 포트를 연 뒤** WAS를 배포하세요(아래 4) 단계에서 연결성을 먼저 확인합니다).

### EC2 / 베어메탈 배포

대상: Amazon Linux 2023 / Ubuntu 22.04+. 아래 명령은 모두 **WAS 호스트**에서 실행합니다.

**1) Python 3.12 + 빌드 의존성 설치** — gcc·MySQL 클라이언트 헤더는 `asyncmy` 빌드에, rsync 는 배포 동기화에 필요

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

**2) 레포 클론**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/was
```

**3) 환경변수 파일 작성** — db·cache 호스트 주소와 JWT 시크릿을 채웁니다
```bash
sudo mkdir -p /etc/mini-commerce
sudo cp deploy/env.example /etc/mini-commerce/was.env
sudo chmod 600 /etc/mini-commerce/was.env
sudo nano /etc/mini-commerce/was.env     # 아래 3개 값을 실제 값으로:
#   DATABASE_URL=mysql+asyncmy://minicommerce:<pw>@<DB_HOST>:3306/minicommerce
#   REDIS_URL=redis://<CACHE_HOST>:6379/0
#   JWT_SECRET_KEY=...    ← `openssl rand -hex 32` 결과를 붙여넣기
```
`<pw>` 는 db 티어에서 설정한 앱 유저 비밀번호, `<DB_HOST>`/`<CACHE_HOST>` 는 각 호스트의 **사설 IP**.

**4) (배포 전) 데이터 티어 연결성 점검** — WAS는 db·cache 가 닿지 않으면 부팅 실패하므로 **먼저 확인**합니다
```bash
nc -zv <DB_HOST> 3306      # → 'succeeded!' 여야 함
nc -zv <CACHE_HOST> 6379   # → 'succeeded!' 여야 함
```
→ 둘 중 하나라도 실패하면 그 데이터 티어 호스트의 **방화벽**부터 점검하세요
([db](../db/README.md) / [cache](../cache/README.md) README 의 방화벽 단계). 여기서 막힌 채로 배포하면
WAS가 크래시 루프에 빠집니다.

**5) 배포 실행**
```bash
# 최초 배포: 데모 데이터 시드 포함(유저+상품). 이후 재배포는 RUN_SEED 생략.
sudo RUN_SEED=true bash deploy/deploy.sh
```
`deploy.sh` 는 ① 소스를 `/opt/mini-commerce-was` 로 동기화 → ② venv 생성·앱 설치 →
③ `alembic upgrade head`(테이블 생성) → ④ (RUN_SEED 시) 데모 데이터 시드 → ⑤ systemd 유닛 설치 후
`mini-commerce-was` 기동, 순서로 진행합니다.
→ 예상 출력: 마지막에 systemd 기동 로그, 에러 없이 종료.

**6) 호스트 방화벽 열기 (8000 ← web 호스트만)** — 클라우드 보안그룹과 **별개로** OS 방화벽도 열어야 합니다
> ⚠️ **Ubuntu** 인스턴스는 기본 iptables 끝에 `REJECT all ... icmp-host-prohibited` 가 있어 8000 이
> 막힙니다. 이러면 WAS 자체는 정상이어도 web 에서 504 가 납니다.

Ubuntu (iptables):
```bash
sudo iptables -L INPUT -n --line-numbers                                 # 끝의 REJECT 줄 번호(<N>) 확인
sudo iptables -I INPUT <N> -p tcp -s <WEB_IP> --dport 8000 -j ACCEPT     # REJECT 위에 ACCEPT 삽입
sudo netfilter-persistent save                                           # 재부팅 후에도 유지(/etc/iptables/rules.v4)
```
Ubuntu(ufw): `sudo ufw allow from <WEB_IP> to any port 8000 proto tcp` ·
AL2023(firewalld): `sudo firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=<WEB_IP> port port=8000 protocol=tcp accept' && sudo firewall-cmd --reload`

**7) 검증**
```bash
systemctl status mini-commerce-was            # active (running) 인지
sudo ss -ltnp | grep ':8000'                  # → 0.0.0.0:8000 (127.0.0.1 이면 web에서 못 붙음)
sudo journalctl -u mini-commerce-was -n 50    # 정상 로그 흐름 확인 (아래)
curl -f http://localhost:8000/healthz/live    # liveness(프로세스 생존) → 200
curl -s http://localhost:8000/healthz/ready   # → {"status":"ready","checks":{"db":"ok","redis":"ok"}}
curl -s http://localhost:8000/version         # 버전 / git_commit / build_time
```
→ 정상 부팅 시 `journalctl` 로그 흐름: `db_pool_ready` → `redis_ready` → `app_started`.
부팅에 실패하면(`Worker failed to boot`) 거의 항상 4) 의 db/cache 연결 문제이니 그 로그(`...Error`)를 보세요.

엔드포인트 구분:
- **`/healthz/live`** — 프로세스가 살아있으면 200(의존성 점검 안 함). k8s liveness probe 용.
- **`/healthz/ready`** — db·cache 가 모두 reachable 할 때만 `ready`(200), 부팅 후 데이터 티어가 끊기면
  `degraded`. readiness probe / 로드밸런서 헬스체크에 적합.
- **`/metrics`** — Prometheus 포맷 메트릭(헬스 엔드포인트는 집계에서 제외).

**데모 계정**(`RUN_SEED=true` 로 시드된 경우):

| 역할 | 이메일 | 비밀번호 |
|------|--------|----------|
| admin | `admin@minicommerce.local` | `Admin1234!` |
| user | `alice@minicommerce.local` | `Alice1234!` |
| user | `bob@minicommerce.local` | `Bob1234!` |

### 마이그레이션 · 시드 소유권
앱이 스키마의 source of truth 입니다. 마이그레이션은 `alembic/` 에 있고 `deploy.sh` 에서
실행됩니다(`RUN_MIGRATIONS_ON_START=false` 로 부팅 시 워커 경합 방지). 데모 유저는 bcrypt
해시가 필요하므로 유저 시드는 db 티어 SQL 이 아니라 여기 Python(`deploy/seed.py`)에서 합니다.

### Docker 배포

`Dockerfile` 이 베어메탈과 동일한 Gunicorn 이미지(`:8000`)를 빌드합니다. db·cache 티어 호스트를
가리키는 `DATABASE_URL` / `REDIS_URL` 을 주입하면 됩니다.

> ⚠️ **베어메탈과 달리 Docker 에는 `deploy.sh` 가 없습니다.** 즉 컨테이너 CMD 는 Gunicorn 만
> 실행하고 **마이그레이션을 자동으로 돌리지 않습니다.** 최초 기동 시 스키마(테이블)를 만들려면
> 아래처럼 **`RUN_MIGRATIONS_ON_START=true`**(부팅 시 `alembic upgrade head` 실행)와,
> 데모 데이터가 필요하면 **`SEED_ON_START=true`** 를 함께 켜야 합니다. 이를 생략하면 테이블이
> 없는 상태로 떠서 모든 API 가 실패합니다.

**1) 이미지 빌드**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/was
docker build -t mini-commerce-was .
```

**2) 환경변수 파일 준비** (베어메탈과 동일한 `env.example` 사용)
```bash
cp deploy/env.example was.env
# was.env 편집: DATABASE_URL / REDIS_URL 을 db·cache 호스트로, JWT_SECRET_KEY 설정
#   DATABASE_URL=mysql+asyncmy://minicommerce:<pw>@<DB_HOST>:3306/minicommerce
#   REDIS_URL=redis://<CACHE_HOST>:6379/0
```

**3) 최초 기동** — 부팅 시 마이그레이션 + 시드를 켜서 실행
```bash
docker run -d --name mini-commerce-was -p 8000:8000 \
    --env-file was.env \
    -e RUN_MIGRATIONS_ON_START=true \
    -e SEED_ON_START=true \
    mini-commerce-was
```
이미지는 Gunicorn 워커 2개로 뜨고 각 워커가 부팅 시 마이그레이션을 시도하지만, 두 번째 워커가
만나는 "already exists" 오류는 무시되도록 처리되어 있어(`app/main.py`) 안전합니다.

**4) 이후 재배포** — 스키마가 이미 있으므로 두 플래그를 끄고(=`env.example` 기본값 `false`) 실행
```bash
docker run -d --name mini-commerce-was -p 8000:8000 --env-file was.env mini-commerce-was
```

**5) 검증** — 이미지에 `HEALTHCHECK`(`/healthz/ready`)가 내장되어 있습니다
```bash
docker ps                                      # STATUS 가 healthy 인지 확인
curl -f http://localhost:8000/healthz/ready    # db·cache reachable 이면 200
```
> Docker 라도 베어메탈과 동일하게 ① db·cache 가 먼저 떠서 `nc -zv <DB_HOST> 3306` / `nc -zv <CACHE_HOST> 6379`
> 가 통과해야 컨테이너가 정상 기동하고, ② web 에서 붙으려면 **호스트 8000 방화벽**을 web 호스트에 열어야
> 합니다(위 베어메탈 6) 단계와 동일).
