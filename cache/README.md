# Mini Commerce — Cache Tier (Redis 7)

Mini Commerce 멀티 티어 배포의 **캐시/세션 티어**입니다. **WAS 티어**에 Redis 7 을 제공합니다
(장바구니 저장, 7일 TTL). **db**(MySQL) 티어와는 별도 호스트로 분리되어 있습니다. **관리형**(Amazon
ElastiCache)과 **설치형**(베어메탈/EC2 또는 Docker) 배포를 모두 지원합니다.

```
cache/
├── baremetal/
│   ├── install-redis.sh        # Redis 7 설치 + 설정 적용 + 기동
│   └── redis.conf              # appendonly yes, maxmemory 128mb, allkeys-lru
├── docker/
│   └── docker-compose.yml      # 단독 Redis 7
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

### 레포 클론 (설치형 공통)
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git
cd mini-commerce-3tier/cache
```

> ⚠️ **WAS는 Redis가 먼저 떠 있어야 부팅됩니다.** WAS는 기동 시 `redis.ping()` 으로 캐시 연결을 확인하고,
> 닿지 않으면 워커가 부팅에 실패해 systemd 가 크래시 루프에 빠집니다([`../was/README.md`](../was/README.md)).
> 따라서 **cache 를 먼저 띄우고 6379 를 WAS 호스트에 연 다음** WAS를 배포하세요.

### 설치형 — Docker
```bash
cd docker
docker compose up -d
docker compose exec redis redis-cli ping   # → PONG
```
`redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru` 로
구동하고 WAS 티어용으로 6379 노출.
> Docker 라도 **호스트 방화벽**은 따로입니다 — 아래 3) 단계로 6379 를 WAS 호스트에 열어야 합니다.

### 설치형 — 베어메탈 / EC2

대상: Ubuntu 22.04+ / Amazon Linux 2023. 아래 명령은 모두 **cache 호스트**에서 실행합니다.

**1) 설치 스크립트 실행** — Redis 7 설치 + `redis.conf`(AOF on, 128MB 상한, LRU 제거) 적용 + 서비스 기동
```bash
sudo bash baremetal/install-redis.sh
```
→ 예상 출력: 마지막에 `PONG` 과 `[install] Done.`

**2) 로컬 ping** — Redis 가 응답하는지 확인
```bash
redis-cli ping
```
→ 예상 출력: `PONG`

**3) 리스닝 확인** — Redis 가 외부 인터페이스(`0.0.0.0`)에 떠 있어야 WAS가 원격 접속할 수 있습니다
```bash
sudo ss -ltnp | grep 6379
```
→ 예상 출력: `LISTEN 0 ... 0.0.0.0:6379 ...`

**4) 호스트 방화벽 열기 (6379 ← WAS 호스트만)** — 클라우드 보안그룹과 **별개로** OS 방화벽도 열어야 합니다
> ⚠️ **Ubuntu** 인스턴스는 기본 iptables 끝에 `REJECT all ... icmp-host-prohibited` 가 있어 6379 가
> 막힙니다. 보안그룹만 열고 끝내면 WAS에서 접속이 안 되고 WAS가 부팅 실패합니다.

Ubuntu (iptables):
```bash
sudo iptables -L INPUT -n --line-numbers                                 # 끝의 REJECT 줄 번호(<N>) 확인
sudo iptables -I INPUT <N> -p tcp -s <WAS_IP> --dport 6379 -j ACCEPT     # REJECT 위에 ACCEPT 삽입
sudo netfilter-persistent save                                           # 재부팅 후에도 유지(/etc/iptables/rules.v4)
```
Ubuntu (ufw 를 쓰는 경우):
```bash
sudo ufw allow from <WAS_IP> to any port 6379 proto tcp
```
Amazon Linux 2023 (firewalld):
```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=<WAS_IP> port port=6379 protocol=tcp accept'
sudo firewall-cmd --reload
```
→ 검증: WAS 호스트에서 `nc -zv <CACHE_HOST> 6379` 가 `succeeded!`, 그리고
`redis-cli -h <CACHE_HOST> ping` 이 `PONG` 이면 통과(WAS 호스트에 redis-cli 가 없으면
`sudo apt-get install -y redis-tools` 또는 `sudo dnf install -y redis`).

#### 네트워크 보안
WAS 티어는 **별도 호스트**에서 접속하므로 Redis 가 사설망에서 reachable 해야 합니다. `redis.conf`
기본값은 `bind 0.0.0.0` + `protected-mode no` 이며, 이는 **엄격한 보안그룹 뒤에서만** 안전합니다.
**6379 는 WAS 티어에만** 허용(보안그룹/방화벽)하고 절대 인터넷에 노출하지 마세요. 필요 시
`requirepass` 를 설정하고 `redis://:<pw>@<host>:6379/0` 형식을 사용하세요.

### WAS 티어 연결
```
REDIS_URL=redis://<이 호스트>:6379/0
```