# Cache Tier — 관리형 (Amazon ElastiCache for Redis 7)

설치형 Redis 호스트 대신 ElastiCache 를 사용합니다. WAS 티어의 연결 방식은 완전히
동일하며, `REDIS_URL` 의 호스트만 ElastiCache 기본(primary) 엔드포인트로 바뀝니다.

## 1. 클러스터 생성
- 엔진: **Redis 7.x**.
- 노드 타입: `cache.t3.micro`(데모) 또는 그 이상.
- 클러스터 모드: 이 앱은 **비활성화**로 충분(단일 primary; HA 가 필요하면 복제본 추가).
- 복제본 수: 0(데모) 또는 1개 이상(운영).
- **서브넷 그룹**: 프라이빗 서브넷만; 퍼블릭 액세스 비활성화.

## 2. 파라미터 (설치형 옵션과 일치)
원본 compose 는 Redis 를
`--appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru` 로 구동했습니다.
ElastiCache 에서 `maxmemory` 는 노드 타입으로 결정되므로, 정책은 커스텀 파라미터
그룹(패밀리 `redis7`)으로 설정하세요:

| 파라미터 | 값 |
|-----------|-------|
| `maxmemory-policy` | `allkeys-lru` |
| `appendonly` | `yes` (또는 내구성 요구에 따라 AOF 활성화 / 스냅샷 사용) |

장바구니 저장소는 7일 TTL(`redis_cart_ttl_seconds`)을 사용하므로, 메모리 부족 시
`allkeys-lru` 제거 정책은 허용 가능합니다.

## 3. 보안그룹
- 인바운드 **6379** 는 **WAS 티어 보안그룹에서만**.
- 인터넷에서의 인바운드 없음.

## 4. WAS 티어 연결
WAS 의 `was.env` 에:
```
REDIS_URL=redis://<elasticache-primary-endpoint>:6379/0
```
전송 중 암호화(TLS)나 인증 토큰을 활성화하면:
```
REDIS_URL=rediss://:<auth-token>@<endpoint>:6379/0
```

## 5. 참고
- 스키마/시드 불필요 — 여기서 Redis 는 순수 캐시/세션 저장소(장바구니 데이터)입니다.
- 캐시가 유실되어도 진행 중 장바구니만 사라지고, 주문은 db 티어에 남습니다.
