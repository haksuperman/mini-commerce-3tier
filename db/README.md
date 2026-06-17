# Mini Commerce — Data Tier (MySQL 8)

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
docker compose ps          # STATUS 가 healthy 가 될 때까지 대기
```
`01-init.sql` 이 최초 부팅 시 자동 실행됩니다(DB + 유저 + 권한 생성). WAS 티어용으로 3306 노출.
> Docker 라도 **호스트 방화벽**은 따로입니다 — 베어메탈과 동일하게 아래 3) 단계로 3306 을 WAS 호스트에
> 열어야 다른 인스턴스의 WAS가 접속할 수 있습니다.

### 설치형 — 베어메탈 / EC2

대상: Ubuntu 22.04+ / Amazon Linux 2023. 아래 명령은 모두 **DB 호스트**에서 실행합니다.

**1) 설치 스크립트 실행** — MySQL 8 설치 + `my.cnf`(utf8mb4) 적용 + 서비스 기동 + DB·앱유저·권한 생성을 한 번에
```bash
sudo MYSQL_APP_PASSWORD='<pw>' bash baremetal/install-mysql.sh
```
→ 예상 출력: 마지막에 `[install] Done.` 과 `App user 'minicommerce' can access DB 'minicommerce'.`
`<pw>` 는 강력한 비밀번호로 바꾸세요. 이후 WAS `DATABASE_URL` 에 **같은 값**을 넣습니다.

**2) 리스닝 확인** — MySQL 이 외부 인터페이스(`0.0.0.0`)에 떠 있어야 WAS가 원격 접속할 수 있습니다
```bash
sudo ss -ltnp | grep 3306
```
→ 예상 출력: `LISTEN 0 ... 0.0.0.0:3306 ...` (만약 `127.0.0.1:3306` 이면 `my.cnf` 의 `bind-address` 확인)

**3) 호스트 방화벽 열기 (3306 ← WAS 호스트만)** — 클라우드 보안그룹과 **별개로** OS 방화벽도 열어야 합니다
> ⚠️ **Ubuntu** 인스턴스는 기본 iptables 규칙 끝에 `REJECT all ... icmp-host-prohibited` 가 있어
> 3306 이 막힙니다. 보안그룹만 열고 끝내면 WAS에서 접속이 안 됩니다.

Ubuntu (iptables):
```bash
sudo iptables -L INPUT -n --line-numbers                                 # 끝의 REJECT 줄 번호(<N>) 확인
sudo iptables -I INPUT <N> -p tcp -s <WAS_IP> --dport 3306 -j ACCEPT     # REJECT 위에 ACCEPT 삽입
sudo netfilter-persistent save                                           # 재부팅 후에도 유지(/etc/iptables/rules.v4)
```
Ubuntu (ufw 를 쓰는 경우):
```bash
sudo ufw allow from <WAS_IP> to any port 3306 proto tcp
```
Amazon Linux 2023 (firewalld):
```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=<WAS_IP> port port=3306 protocol=tcp accept'
sudo firewall-cmd --reload
```
→ 검증: WAS 호스트에서 `nc -zv <DB_HOST> 3306` 가 `succeeded!` 면 통과.

**4) 로컬 로그인 확인** — 앱 유저로 DB에 붙는지 점검
```bash
mysql -u minicommerce -p minicommerce -e 'SELECT 1;'
```
→ 예상 출력: `1` 한 줄. (`Access denied` 면 `<pw>` 또는 1) 단계의 유저 생성 확인)

> **MySQL 베어메탈 참고:** 신규 설치 시 root 인증은 배포판마다 다릅니다(Ubuntu `auth_socket`, MySQL
> community 임시 비밀번호). 단 위 스크립트가 **앱 유저**를 `mysql_native_password`(asyncmy 드라이버 요구)로
> 이미 생성하므로, root 로 들어갈 필요 없이 앱 유저 로그인만 확인하면 됩니다.

### 프로비저닝 후 (WAS 배포 시)
1. **WAS** 호스트에서 `DATABASE_URL=mysql+asyncmy://minicommerce:<pw>@<DB_HOST>:3306/minicommerce` 설정 후
   `alembic upgrade head` 로 테이블을 만듭니다. 상세 절차는 [`../was/README.md`](../was/README.md).
2. (선택) 상품 시드 — **WAS 마이그레이션 이후** 실행:
   ```bash
   mysql -h <DB_HOST> -u minicommerce -p minicommerce < init/02-seed-products.sql
   ```
   데모 **유저**는 bcrypt 해시가 필요하므로 WAS 티어(`deploy/seed.py`)가 시드합니다.

### 보안
3306 은 **WAS 티어에만** 노출하세요(클라우드 보안그룹 **+ 호스트 방화벽** 둘 다). 절대 인터넷에 열지
마세요. 강력한 앱 유저 비밀번호를 쓰고 WAS `DATABASE_URL` 과 동기화하세요.
