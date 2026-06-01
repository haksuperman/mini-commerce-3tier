# Mini Commerce — Web Tier (nginx + React SPA)

🇰🇷 [한국어](#한국어) · 🇬🇧 [English](#english)

---

## 한국어

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

---

## English

The **web tier** of the Mini Commerce multi-tier deployment. Serves the React/Vite
static SPA via nginx and reverse-proxies `/api/` requests to the **WAS** tier
(FastAPI/Gunicorn). The browser only ever talks to this tier, so **no CORS** is
required and the SPA uses **relative** `/api/v1` paths.

```
web/
├── app/                              # React/Vite SPA source
├── deploy/
│   ├── nginx/mini-commerce-web.conf  # static serving + /api/ reverse proxy
│   ├── deploy.sh                     # build → publish → render conf → reload
│   └── env.example                   # WAS_UPSTREAM, VITE_API_BASE_URL=""
├── README.md
└── .gitignore
```

### Architecture
```
browser ──http──> web (nginx :80) ──/api/ proxy──> was (FastAPI :8000)
                       └── serves static SPA from /var/www/mini-commerce
```
Security group: web `80/443` ← internet · was `8000` ← web SG only.

### EC2 / bare-metal deploy

Tested target: Amazon Linux 2023 / Ubuntu 22.04+.

**1) Install nginx + Node 20**

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

**2) Clone + configure**
```bash
git clone https://github.com/haksuperman/mini-commerce-3tier.git && cd mini-commerce-3tier/web
cp deploy/env.example deploy/.env
# edit deploy/.env → set WAS_UPSTREAM to the WAS private IP, e.g. 10.0.2.10:8000
# keep VITE_API_BASE_URL empty (relative paths)
```

**3) Build + deploy**
```bash
sudo -E bash deploy/deploy.sh
```
Runs `npm ci`, builds with `VITE_API_BASE_URL=""`, copies `app/dist/` to
`/var/www/mini-commerce`, renders the nginx server block (substituting
`__WAS_UPSTREAM__`), then `nginx -t` and reloads.

**4) Verify**
```bash
curl -I http://localhost/                 # SPA index → 200
curl -s http://localhost/api/v1/products  # proxied to WAS → product JSON
```
Open `http://<web-public-ip>/` in a browser; the product list loads via the
relative `/api/v1/products` path with no CORS errors.

### Docker (optional)
`app/Dockerfile` builds an unprivileged nginx image serving the SPA on `:8080`.
Note that the bundled `app/nginx.conf` is the **standalone** SPA config (no
reverse proxy). For the multi-tier reverse-proxy setup use
`deploy/nginx/mini-commerce-web.conf` on bare metal as above.
