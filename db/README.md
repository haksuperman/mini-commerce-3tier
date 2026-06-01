# Mini Commerce — Data Tier (MySQL 8)

🇰🇷 [한국어](#한국어) · 🇬🇧 [English](#english)

---

## 한국어

Mini Commerce 멀티 티어 배포의 **영속 데이터 티어**입니다. **WAS 티어**에 MySQL 8 데이터베이스를
제공합니다. **관리형**(Amazon RDS)과 **설치형**(베어메탈/EC2 또는 Docker) 배포를 모두 지원합니다.

> 데이터베이스 **스키마(테이블)** 는 WAS 티어가 Alembic 으로 소유합니다. 이 티어는 서버·DB·앱
> 유저·권한 프로비저닝만 담당합니다. 상품 시드 SQL 도 제공하지만 **WAS 마이그레이션 이후**에
> 실행해야 합니다.

```
db/
├── baremetal/
│   ├── install-mysql.sh        # MySQL 8 설치 + init 적용 + 설정
│   └── my.cnf                  # utf8mb4 / utf8mb4_unicode_ci 서버 설정
├── docker/
│   └── docker-compose.yml      # 단독 MySQL 8
├── init/
│   ├── 01-init.sql             # DB + 앱 유저 + 권한 (최초 부팅 시 자동 실행)
│   └── 02-seed-products.sql    # 선택 상품 시드 (WAS 마이그레이션 후 실행)
├── managed/README.md           # Amazon RDS MySQL 8 가이드
├── README.md
└── .gitignore
```

### 배포 방식 선택
| | 관리형(RDS) | 설치형(Docker / 베어메탈) |
|--|------------|---------------------------|
| 운영 | AWS 가 패치/백업 관리 | 직접 관리 |
| 비용 | 높음 | 낮음 |
| 설정 | `managed/README.md` | 아래 참조 |

### 레포 클론 (설치형 공통)
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/db
```

### 설치형 — Docker
```bash
cd docker
MYSQL_ROOT_PASSWORD=... MYSQL_PASSWORD=... docker compose up -d
docker compose ps          # healthy 대기
```
`01-init.sql` 이 최초 부팅 시 자동 실행됩니다(DB + 유저 + 권한 생성). WAS 티어용으로 3306 노출.

### 설치형 — 베어메탈 / EC2
```bash
sudo MYSQL_APP_PASSWORD='strong-password' bash baremetal/install-mysql.sh
```
MySQL 8 설치, `my.cnf`(utf8mb4) 적용, 서비스 기동, DB + 앱 유저 생성.

### 프로비저닝 후
1. **WAS** 호스트에서 `DATABASE_URL=...@<이 호스트>:3306/minicommerce` 설정 후
   `alembic upgrade head` 실행(테이블 생성).
2. (선택) 상품 시드:
   ```bash
   mysql -h <DB_HOST> -u minicommerce -p minicommerce < init/02-seed-products.sql
   ```
   데모 **유저**는 bcrypt 해시가 필요하므로 WAS 티어(`deploy/seed.py`)가 시드합니다.

### 보안
3306 은 **WAS 티어에만** 노출하세요(보안그룹/방화벽). 절대 인터넷에 열지 마세요. 강력한 앱 유저
비밀번호를 쓰고 WAS `DATABASE_URL` 과 동기화하세요.

---

## English

The **persistent data tier** of the Mini Commerce multi-tier deployment. Provides a
MySQL 8 database for the **WAS** tier. Supports both **managed** (Amazon RDS)
and **self-managed** (bare-metal/EC2 or Docker) deployments.

> The database **schema** (tables) is owned by the WAS tier via Alembic. This
> tier only provisions the server, database, app user, and grants. Product seed
> SQL is provided but must run **after** WAS migrations.

```
db/
├── baremetal/
│   ├── install-mysql.sh        # install MySQL 8 + apply init + config
│   └── my.cnf                  # utf8mb4 / utf8mb4_unicode_ci server config
├── docker/
│   └── docker-compose.yml      # standalone MySQL 8
├── init/
│   ├── 01-init.sql             # DB + app user + grants (auto-runs at first boot)
│   └── 02-seed-products.sql    # OPTIONAL product seed (run after WAS migrations)
├── managed/README.md           # Amazon RDS MySQL 8 guide
├── README.md
└── .gitignore
```

### Choosing a deployment
| | Managed (RDS) | Self-managed (Docker / bare metal) |
|--|---------------|-------------------------------------|
| Ops | AWS handles patching/backups | You manage everything |
| Cost | Higher | Lower |
| Setup | `managed/README.md` | below |

### Clone (common to self-managed)
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/db
```

### Self-managed — Docker
```bash
cd docker
MYSQL_ROOT_PASSWORD=... MYSQL_PASSWORD=... docker compose up -d
docker compose ps          # wait for healthy
```
`01-init.sql` runs automatically on first boot (creates DB + user + grants).
Port 3306 is exposed for the WAS tier.

### Self-managed — bare metal / EC2
```bash
sudo MYSQL_APP_PASSWORD='strong-password' bash baremetal/install-mysql.sh
```
Installs MySQL 8, drops in `my.cnf` (utf8mb4), starts the service, and creates the
DB + app user.

### After provisioning
1. On the **WAS** host set `DATABASE_URL=...@<this-host>:3306/minicommerce` and
   run `alembic upgrade head` (creates tables).
2. (Optional) Seed products:
   ```bash
   mysql -h <DB_HOST> -u minicommerce -p minicommerce < init/02-seed-products.sql
   ```
   Demo **users** are seeded by the WAS tier (`deploy/seed.py`), since they need
   bcrypt password hashes.

### Security
Expose 3306 **only** to the WAS tier (security group / firewall), never the
internet. Use a strong app-user password and keep it in sync with the WAS
`DATABASE_URL`.
