# Mini Commerce — Web Tier (nginx + React SPA)

Mini Commerce 멀티 티어 배포의 **web 티어**입니다. nginx 로 React/Vite 정적 SPA 를 서빙하고,
`/api/` 요청을 **WAS 티어**(FastAPI/Gunicorn)로 **리버스 프록시**합니다. 브라우저는 이 web 티어만
호출하므로 **CORS 가 필요 없고**, SPA 는 `/api/v1` **상대경로**를 사용합니다.

> **배포 순서**: ① db → ② cache → ③ was → **④ web** 중 **4번째(마지막)**.
> **선행 조건: was 가 정상 기동**되어 `curl http://<WAS_IP>:8000/api/v1/products` 가 성공해야 합니다.

## 구성
```
web/
├── app/                              # React/Vite SPA 소스
├── deploy/
│   ├── nginx/mini-commerce-web.conf  # 정적 서빙 + /api/ 리버스 프록시
│   ├── deploy.sh                     # 빌드 → 배포 → conf 치환 → reload
│   └── env.example                   # WAS_UPSTREAM, VITE_API_BASE_URL=""
├── README.md
└── .gitignore
```

## 아키텍처
```
브라우저 ──http──> web(nginx :80) ──/api/ 프록시──> was(FastAPI :8000)
                       └ 정적 SPA 서빙 (/var/www/mini-commerce)
```
**포트 정책**: web `80/443` ← 인터넷 (web → was `8000` 은 아웃바운드) — AWS 환경이라면 Security Group/NACL,
그리고 호스트 OS 방화벽 **둘 다** 적용합니다.

## 베어메탈 배포

대상: Amazon Linux 2023 / Ubuntu 22.04+. 아래 명령은 모두 **web 호스트**에서 실행합니다.

**1) nginx + Node 20 설치** — nginx 는 서빙/프록시, Node 20·gettext(envsubst)는 SPA 빌드·설정 렌더링에 필요

Amazon Linux 2023:
```bash
sudo dnf install -y nginx gettext
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs
sudo systemctl enable --now nginx
```
Ubuntu:
```bash
sudo apt-get update && sudo apt-get install -y nginx gettext
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs
sudo systemctl enable --now nginx
```

**2) 클론 + 설정** — `WAS_UPSTREAM` 에 **WAS 호스트의 사설 IP**(web 자신이 아님)를 넣는 게 핵심
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/web
cp deploy/env.example deploy/.env
sudo nano deploy/.env
#   WAS_UPSTREAM=<WAS_IP>:8000      ← 예: 10.0.2.10:8000 (반드시 WAS 호스트 사설 IP)
#   VITE_API_BASE_URL=             ← 빈 값 유지(상대경로 /api/v1 사용)
```
> ⚠️ `hostname -I` 로 **이 web 호스트의 IP** 를 확인하세요. `WAS_UPSTREAM` 에 실수로 web 자신의 IP 를 넣으면
> nginx 가 자기 자신 8000(없음)으로 프록시해 504 가 납니다.

**3) 빌드 + 배포**
```bash
sudo -E bash deploy/deploy.sh
```
`deploy.sh` 는 ① `npm ci` → ② `VITE_API_BASE_URL=""` 로 빌드 → ③ `app/dist/` 를 `/var/www/mini-commerce` 로
복사 → ④ nginx 서버 블록 렌더링(`__WAS_UPSTREAM__` 치환) → ⑤ `nginx -t` 후 reload, 순서로 진행합니다.
→ 예상 출력: 마지막에 `[deploy] Done. Web tier serving ...`.
> **정상이지만 놀라는 출력 2가지** — 둘 다 배포 실패가 아닙니다.
> - `npm` 빌드 중 `N vulnerabilities (... critical)` : npm 의존성 트리의 알려진 취약점 **알림**일 뿐 빌드는 성공.
>   대부분 빌드/테스트용 devDependency 라 운영(정적 파일) 노출과 무관. 점검은 `npm audit --omit=dev`.
> - nginx `conflicting server name "_" ... ignored` : 배포판 기본 서버 블록
>   (`/etc/nginx/sites-enabled/default`, 같은 `:80`·`server_name _`)과 겹쳐 나는 경고. 거슬리면 Ubuntu 에서
>   `sudo rm /etc/nginx/sites-enabled/default && sudo systemctl reload nginx` 로 제거하면 사라집니다.

**4) 호스트 방화벽 — 80(필요 시 443)을 인터넷에 허용**
AWS 환경이라면 Security Group/NACL 에서도 80/443 을 허용하세요. 그리고 호스트 OS 방화벽도 엽니다.
> ⚠️ **Ubuntu** 인스턴스는 기본 iptables 끝에 `REJECT all ... icmp-host-prohibited` 가 있어 80 이 막힐 수 있습니다.

Ubuntu(iptables) — 기본 끝의 `REJECT` 위에 ACCEPT 삽입(web 은 인터넷 공개라 소스 제한 없음):
```bash
sudo iptables -L INPUT -n --line-numbers                  # 끝의 REJECT 줄 번호(<N>) 확인
sudo iptables -I INPUT <N> -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save                            # 재부팅 후에도 유지(/etc/iptables/rules.v4)
```
> 대안 — ufw: `sudo ufw allow 80/tcp` ·
> Amazon Linux 2023(firewalld): `sudo firewall-cmd --permanent --add-service=http && sudo firewall-cmd --reload`

**5) 검증** — nginx 는 **`/api/` 경로만** WAS로 프록시합니다(`/healthz` 등은 프록시 안 됨)
```bash
curl -I http://localhost/                  # SPA index → 200
curl -s http://localhost/api/v1/products   # web nginx → WAS 프록시 → 상품 20개 JSON
```
→ `http://<WAS_IP>:8000/...` 는 WAS 를 **직접** 보는 것이고(포트 8000), web 을 통한 확인은
**`/api/v1/products`**(포트 80, `/api/` 경로) 로 합니다. `http://<web>/healthz/...` 처럼 프록시되지 않는
경로/포트로 테스트하면 404·timeout 이 나니 주의하세요.
→ 브라우저로 `http://<web-공인IP>/` 접속 → 상품 목록이 `/api/v1/products` 상대경로로 로드되고 CORS 에러가
없어야 합니다.

## Docker 배포 (선택)
`app/Dockerfile` 은 SPA 를 `:8080` 으로 서빙하는 비특권 nginx 이미지를 빌드합니다. 단, 번들된
`app/nginx.conf` 는 **단독** SPA 설정(리버스 프록시 없음)입니다. 멀티 티어 리버스 프록시 구성은 위처럼
베어메탈에서 `deploy/nginx/mini-commerce-web.conf` 를 사용하세요.

## 다음 단계
마지막 티어입니다. 4서버 전체 흐름과 동작 확인은 [루트 README](../README.md) 의 "한 번에 따라하기" 를 참고하세요.
