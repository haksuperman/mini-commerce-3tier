# Data Tier — 관리형 (Amazon RDS for MySQL 8)

설치형 MySQL 호스트 대신 RDS 를 사용합니다. WAS 티어의 연결 방식은 완전히 동일하며,
`DATABASE_URL` 의 호스트만 RDS 엔드포인트로 바뀝니다.

## 1. RDS 인스턴스 생성
- 엔진: **MySQL 8.0**.
- 인스턴스 클래스: `db.t3.micro`(데모) 또는 그 이상.
- 스토리지: 20 GB gp3, 오토스케일링 선택.
- 다중 AZ: 데모는 off, 운영은 on.
- **퍼블릭 액세스 비활성화**; 프라이빗 서브넷에 배치.

## 2. 파라미터 그룹 (utf8mb4)
앱과 문자셋을 맞추기 위해 커스텀 DB 파라미터 그룹(패밀리 `mysql8.0`)을 생성하세요
(원본 compose 는 `utf8mb4` / `utf8mb4_unicode_ci` 사용):

| 파라미터 | 값 |
|-----------|-------|
| `character_set_server` | `utf8mb4` |
| `collation_server` | `utf8mb4_unicode_ci` |

`default_authentication_plugin` 은 RDS 에서 설정할 수 없지만, `asyncmy` 는 RDS MySQL 8
기본값(`caching_sha2_password`)에서 동작합니다. 인증 문제가 발생하면 앱 유저를
`mysql_native_password` 로 생성하세요(4단계).

## 3. 보안그룹
- 인바운드 **3306** 은 **WAS 티어 보안그룹에서만**(0.0.0.0/0 금지).
- 인터넷에서의 인바운드 없음.

## 4. 데이터베이스 + 앱 유저 생성
마스터 유저로 접속해 실행:
```sql
CREATE DATABASE IF NOT EXISTS minicommerce
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'minicommerce'@'%' IDENTIFIED BY '<strong-password>';
GRANT ALL PRIVILEGES ON minicommerce.* TO 'minicommerce'@'%';
FLUSH PRIVILEGES;
```
(`../init/01-init.sql` 참고.) `products`/`users`/`orders` 테이블은 **WAS** 티어의 Alembic
마이그레이션이 생성하므로 여기서 만들지 마세요.

## 5. WAS 티어 연결
WAS 의 `was.env` 에:
```
DATABASE_URL=mysql+asyncmy://minicommerce:<password>@<rds-endpoint>:3306/minicommerce
```
이후 WAS 호스트에서 `alembic upgrade head`(`deploy/deploy.sh` 경유)를 실행하고,
필요 시 `../init/02-seed-products.sql` 로 상품을 시드하세요.

## 6. 백업
자동 백업(보존 7일)과 유지보수 윈도우를 활성화하세요. RDS 가 패치를 관리하며,
스키마만 (WAS 의 Alembic 으로) 직접 소유합니다.
