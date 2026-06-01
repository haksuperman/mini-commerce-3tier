# Mini Commerce — Cache Tier (Redis 7)

🇰🇷 [한국어](#한국어) · 🇬🇧 [English](#english)

---

## 한국어

Mini Commerce 멀티 티어 배포의 **캐시/세션 티어**입니다. **WAS 티어**에 Redis 7 을 제공합니다
(장바구니 저장, 7일 TTL). **db**(MySQL) 티어와는 별도 호스트로 분리되어 있습니다. **관리형**(Amazon
ElastiCache)과 **설치형**(베어메탈/EC2 또는 Docker) 배포를 모두 지원합니다.

```
cache/
├── baremetal/
│   ├── install-redis.sh        # Redis 7 설치 + 설정 적용 + 기동
│   └── redis.conf              # appendonly yes, maxmemory 128mb, allkeys-lru
├── docker/
│   └── docker-compose.yml      # 단독 Redis 7 (모노레포에서 추출)
├── managed/README.md           # Amazon ElastiCache Redis 7 가이드
├── README.md
└── .gitignore
```

### 역할
WAS 는 `REDIS_URL=redis://<CACHE_HOST>:6379/0` 로만 이 티어를 참조합니다. 장바구니를 저장하며
(`redis_cart_ttl_seconds`, 기본 7일), 캐시가 유실되어도 진행 중 장바구니만 사라지고 확정된 주문은
db 티어에 남습니다.

### 배포 방식 선택
| | 관리형(ElastiCache) | 설치형(Docker / 베어메탈) |
|--|--------------------|---------------------------|
| 운영 | AWS 가 패치/페일오버 관리 | 직접 관리 |
| 비용 | 높음 | 낮음 |
| 설정 | `managed/README.md` | 아래 참조 |

### 설치형 — Docker
```bash
cd docker
docker compose up -d
docker compose exec redis redis-cli ping   # → PONG
```
`redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru` 로
구동하고 WAS 티어용으로 6379 노출.

### 설치형 — 베어메탈 / EC2
```bash
sudo bash baremetal/install-redis.sh
redis-cli ping   # → PONG
```
Redis 7 설치 + `redis.conf`(AOF on, 128MB 상한, LRU 제거) 적용.

#### 네트워크 보안
WAS 티어는 **별도 호스트**에서 접속하므로 Redis 가 사설망에서 reachable 해야 합니다. `redis.conf`
기본값은 `bind 0.0.0.0` + `protected-mode no` 이며, 이는 **엄격한 보안그룹 뒤에서만** 안전합니다.
**6379 는 WAS 티어에만** 허용(보안그룹/방화벽)하고 절대 인터넷에 노출하지 마세요. 필요 시
`requirepass` 를 설정하고 `redis://:<pw>@<host>:6379/0` 형식을 사용하세요.

### WAS 티어 연결
```
REDIS_URL=redis://<이 호스트>:6379/0
```

### 원본
원본 모노레포 `docker-compose.yml`(`redis` 서비스)에서 추출했으며 원본은 수정하지 않았습니다.

---

## English

The **cache/session tier** of the Mini Commerce multi-tier deployment. Provides
Redis 7 for the **WAS** tier (shopping-cart storage with a 7-day TTL). Separated
onto its own host from the **db** (MySQL) tier. Supports both **managed** (Amazon
ElastiCache) and **self-managed** (bare-metal/EC2 or Docker) deployments.

```
cache/
├── baremetal/
│   ├── install-redis.sh        # install Redis 7 + apply config + start
│   └── redis.conf              # appendonly yes, maxmemory 128mb, allkeys-lru
├── docker/
│   └── docker-compose.yml      # standalone Redis 7 (extracted from monorepo)
├── managed/README.md           # Amazon ElastiCache Redis 7 guide
├── README.md
└── .gitignore
```

### Role
WAS references this tier only via `REDIS_URL=redis://<CACHE_HOST>:6379/0`. It
stores shopping carts (`redis_cart_ttl_seconds`, default 7 days). Losing the
cache only drops in-progress carts; persisted orders live in the db tier.

### Choosing a deployment
| | Managed (ElastiCache) | Self-managed (Docker / bare metal) |
|--|------------------------|-------------------------------------|
| Ops | AWS handles patching/failover | You manage everything |
| Cost | Higher | Lower |
| Setup | `managed/README.md` | below |

### Self-managed — Docker
```bash
cd docker
docker compose up -d
docker compose exec redis redis-cli ping   # → PONG
```
Runs `redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy
allkeys-lru` and exposes 6379 for the WAS tier.

### Self-managed — bare metal / EC2
```bash
sudo bash baremetal/install-redis.sh
redis-cli ping   # → PONG
```
Installs Redis 7 and drops in `redis.conf` (AOF on, 128 MB cap, LRU eviction).

#### Network hardening
The WAS tier connects from a **separate host**, so Redis must be reachable on the
private network. `redis.conf` defaults to `bind 0.0.0.0` + `protected-mode no`,
which is only safe behind a strict security group. Restrict **6379 to the WAS
tier only** (security group / firewall) and never expose it to the internet.
Optionally set `requirepass` and use `redis://:<pw>@<host>:6379/0`.

### Wire up the WAS tier
```
REDIS_URL=redis://<this-host>:6379/0
```

### Source
Extracted from the original monorepo `docker-compose.yml` (`redis` service)
without modifying the original.
