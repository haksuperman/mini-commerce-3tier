-- ============================================================
-- Mini Commerce — Data Tier init (MySQL 8)
-- Runs once on first container start (docker-entrypoint-initdb.d).
--
-- The official mysql image already creates MYSQL_DATABASE / MYSQL_USER from
-- env vars. This script makes DB + user + grants EXPLICIT so the same SQL also
-- works on a bare-metal MySQL where those env vars do not apply.
--
-- Schema (tables) is owned by the WAS tier via Alembic — NOT created here.
-- ============================================================

CREATE DATABASE IF NOT EXISTS minicommerce
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Application user. On bare metal, change the password to a strong secret and
-- keep it in sync with the WAS DATABASE_URL.
CREATE USER IF NOT EXISTS 'minicommerce'@'%' IDENTIFIED BY 'localdev';
ALTER USER 'minicommerce'@'%' IDENTIFIED WITH mysql_native_password BY 'localdev';

GRANT ALL PRIVILEGES ON minicommerce.* TO 'minicommerce'@'%';
FLUSH PRIVILEGES;

SELECT 'Mini Commerce DB initialized' AS status;
