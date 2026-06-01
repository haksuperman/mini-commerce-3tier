# Cache Tier — Managed (Amazon ElastiCache for Redis 7)

Using ElastiCache instead of a self-managed Redis host. The WAS tier connects
exactly the same way — only the host in `REDIS_URL` changes to the ElastiCache
primary endpoint.

## 1. Create the cluster
- Engine: **Redis 7.x**.
- Node type: `cache.t3.micro` (demo) or larger.
- Cluster mode: **disabled** is fine for this app (single primary; add a replica
  for HA).
- Number of replicas: 0 (demo) or 1+ (prod).
- **Subnet group**: private subnets only; do not enable public access.

## 2. Parameters (match the self-managed options)
The original compose ran Redis with
`--appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru`.
On ElastiCache `maxmemory` is governed by the node type, so set the policy via a
custom parameter group (family `redis7`):

| Parameter | Value |
|-----------|-------|
| `maxmemory-policy` | `allkeys-lru` |
| `appendonly` | `yes` (or enable AOF / use snapshots per durability needs) |

The cart store uses a 7-day TTL (`redis_cart_ttl_seconds`), so `allkeys-lru`
eviction under memory pressure is acceptable.

## 3. Security group
- Inbound **6379** from the **WAS tier security group only**.
- No inbound from the internet.

## 4. Wire up the WAS tier
In the WAS `was.env`:
```
REDIS_URL=redis://<elasticache-primary-endpoint>:6379/0
```
If you enable in-transit encryption (TLS) or an auth token, use:
```
REDIS_URL=rediss://:<auth-token>@<endpoint>:6379/0
```

## 5. Notes
- No schema/seed needed — Redis is a pure cache/session store here (cart data).
- Losing the cache only drops in-progress carts; orders live in the db tier.
