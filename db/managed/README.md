# Data Tier — Managed (Amazon RDS for MySQL 8)

Using RDS instead of a self-managed MySQL host. The WAS tier connects exactly
the same way — only the host in `DATABASE_URL` changes to the RDS endpoint.

## 1. Create the RDS instance
- Engine: **MySQL 8.0**.
- Instance class: `db.t3.micro` (demo) or larger.
- Storage: 20 GB gp3, autoscaling optional.
- Multi-AZ: off for demo, on for prod.
- **Disable public access**; place it in private subnets.

## 2. Parameter group (utf8mb4)
Create a custom DB parameter group (family `mysql8.0`) so the charset matches
the app (the original compose used `utf8mb4` / `utf8mb4_unicode_ci`):

| Parameter | Value |
|-----------|-------|
| `character_set_server` | `utf8mb4` |
| `collation_server` | `utf8mb4_unicode_ci` |

`default_authentication_plugin` is not settable on RDS, but `asyncmy` works with
RDS MySQL 8 defaults (`caching_sha2_password`). If you hit auth issues, create the
app user with `mysql_native_password` (step 4).

## 3. Security group
- Inbound **3306** from the **WAS tier security group only** (not 0.0.0.0/0).
- No inbound from the internet.

## 4. Create database + app user
Connect as the master user and run:
```sql
CREATE DATABASE IF NOT EXISTS minicommerce
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'minicommerce'@'%' IDENTIFIED BY '<strong-password>';
GRANT ALL PRIVILEGES ON minicommerce.* TO 'minicommerce'@'%';
FLUSH PRIVILEGES;
```
(See `../init/01-init.sql`.) The `products`/`users`/`orders` tables are created by
the **WAS** tier's Alembic migrations — do not create them here.

## 5. Wire up the WAS tier
In the WAS `was.env`:
```
DATABASE_URL=mysql+asyncmy://minicommerce:<password>@<rds-endpoint>:3306/minicommerce
```
Then on the WAS host run `alembic upgrade head` (via `deploy/deploy.sh`), and
optionally seed products with `../init/02-seed-products.sql`.

## 6. Backups
Enable automated backups (retention 7d) and a maintenance window. RDS handles
patching; you only own the schema (via Alembic on WAS).
