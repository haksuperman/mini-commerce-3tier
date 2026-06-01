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

-- Application user (asyncmy needs mysql_native_password).
--
-- In Docker the official mysql image already creates this user from MYSQL_USER /
-- MYSQL_PASSWORD *before* this script runs, so `IF NOT EXISTS` makes the CREATE a
-- no-op and the env-supplied password is preserved. The hardcoded 'localdev'
-- below is only the fallback when the user does NOT already exist (e.g. running
-- this SQL directly on a fresh bare-metal server).
--
-- ⚠️ Do NOT add an unconditional `ALTER USER ... IDENTIFIED BY 'localdev'` here:
-- it would overwrite the MYSQL_PASSWORD set by the Docker image and break the
-- WAS DATABASE_URL. On bare metal, prefer baremetal/install-mysql.sh, which sets
-- the password from MYSQL_APP_PASSWORD.
CREATE USER IF NOT EXISTS 'minicommerce'@'%'
    IDENTIFIED WITH mysql_native_password BY 'localdev';

GRANT ALL PRIVILEGES ON minicommerce.* TO 'minicommerce'@'%';
FLUSH PRIVILEGES;

SELECT 'Mini Commerce DB initialized' AS status;
