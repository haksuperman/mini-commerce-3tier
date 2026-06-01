# Mini Commerce — Web Tier (nginx + React SPA)

Mini Commerce 멀티 티어 배포의 **web 티어**입니다. nginx 로 React/Vite 정적 SPA 를 서빙하고,
`/api/` 요청을 **WAS 티어**(FastAPI/Gunicorn)로 **리버스 프록시**합니다. 브라우저는 이 web 티어만
호출하므로 **CORS 가 필요 없고**, SPA 는 `/api/v1` **상대경로**를 사용합니다.

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

### 아키텍처
```
브라우저 ──http──> web(nginx :80) ──/api/ 프록시──> was(FastAPI :8000)
                       └ 정적 SPA 서빙 (/var/www/mini-commerce)
```
보안그룹: web `80/443` ← 인터넷 · was `8000` ← web SG 만.

### EC2 / 베어메탈 배포

대상: Amazon Linux 2023 / Ubuntu 22.04+

**1) nginx + Node 20 설치**

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

**2) 클론 + 설정**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/web
cp deploy/env.example deploy/.env
# deploy/.env 편집 → WAS_UPSTREAM 을 WAS 사설 IP 로, 예: 10.0.2.10:8000
# VITE_API_BASE_URL 은 빈 값 유지(상대경로)
```

**3) 빌드 + 배포**
```bash
sudo -E bash deploy/deploy.sh
```
`npm ci` → `VITE_API_BASE_URL=""` 로 빌드 → `app/dist/` 를 `/var/www/mini-commerce` 로 복사 →
nginx 서버 블록 렌더링(`__WAS_UPSTREAM__` 치환) → `nginx -t` 후 reload.

**4) 검증**
```bash
curl -I http://localhost/                 # SPA index → 200
curl -s http://localhost/api/v1/products  # WAS 로 프록시 → 상품 JSON
```
브라우저로 `http://<web-공인IP>/` 접속 → 상품 목록이 `/api/v1/products` 상대경로로 로드되고
CORS 에러가 없어야 합니다.

### Docker (선택)
`app/Dockerfile` 은 SPA 를 `:8080` 으로 서빙하는 비특권 nginx 이미지를 빌드합니다. 단, 번들된
`app/nginx.conf` 는 **단독** SPA 설정(리버스 프록시 없음)입니다. 멀티 티어 리버스 프록시 구성은
위처럼 베어메탈에서 `deploy/nginx/mini-commerce-web.conf` 를 사용하세요.
