-- ============================================================
-- Mini Commerce — Product seed (OPTIONAL, MANUAL)
--
-- ⚠️ Run this ONLY AFTER the WAS tier has applied its Alembic migrations
--    (`alembic upgrade head`), which create the `products` table. This file is
--    intentionally NOT auto-mounted into docker-entrypoint-initdb.d, because at
--    first MySQL boot the table does not exist yet.
--
-- Idempotent: each row inserts only if a product with the same name is absent.
-- USER seeding is NOT here — demo users need bcrypt hashes and are seeded by the
-- WAS tier (deploy/seed.py).
--
-- Usage:
--   mysql -h <DB_HOST> -u minicommerce -p minicommerce < init/02-seed-products.sql
-- ============================================================

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT
  'Wireless Bluetooth Headphones' AS name,
  'Premium noise-cancelling wireless headphones with 30h battery life.' AS description,
  89.99 AS price, 50 AS stock, 'Electronics' AS category,
  'https://picsum.photos/seed/WirelessBluetoothHeadphones/400/300' AS image_url) AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'USB-C Charging Hub 7-in-1',
  'Expand your laptop ports with 4K HDMI, USB 3.0, SD card reader, and more.',
  34.99, 100, 'Electronics',
  'https://picsum.photos/seed/USB-CChargingHub7-in-1/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Mechanical Keyboard TKL',
  'Tenkeyless mechanical keyboard with Cherry MX Red switches, RGB backlight.',
  129.99, 30, 'Electronics',
  'https://picsum.photos/seed/MechanicalKeyboardTKL/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT '27-inch 4K Monitor',
  'IPS panel, 144Hz refresh rate, HDR400 support, USB-C delivery.',
  399.99, 15, 'Electronics',
  'https://picsum.photos/seed/27-inch4KMonitor/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Portable SSD 1TB',
  'Read up to 1050MB/s, shock-resistant, USB 3.2 Gen 2.',
  74.99, 60, 'Electronics',
  'https://picsum.photos/seed/PortableSSD1TB/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Classic Cotton T-Shirt (White)',
  '100% organic cotton, pre-shrunk, available in S/M/L/XL.',
  19.99, 200, 'Clothing',
  'https://picsum.photos/seed/ClassicCottonT-Shirt(White)/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Slim Fit Chino Pants',
  'Stretch chino fabric, 5-pocket design, machine washable.',
  49.99, 80, 'Clothing',
  'https://picsum.photos/seed/SlimFitChinoPants/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Running Sneakers Pro',
  'Lightweight mesh upper, responsive foam midsole, reflective accents.',
  119.99, 45, 'Clothing',
  'https://picsum.photos/seed/RunningSneakersPro/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Hooded Fleece Jacket',
  'Anti-pilling fleece, full-zip, kangaroo pocket, thumb holes.',
  79.99, 60, 'Clothing',
  'https://picsum.photos/seed/HoodedFleeceJacket/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Clean Code',
  'A handbook of agile software craftsmanship by Robert C. Martin.',
  35.99, 40, 'Books',
  'https://picsum.photos/seed/CleanCode/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Designing Data-Intensive Applications',
  'The big ideas behind reliable, scalable, and maintainable systems.',
  42.99, 35, 'Books',
  'https://picsum.photos/seed/DesigningData-IntensiveApplications/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'The Pragmatic Programmer',
  'Your journey to mastery — 20th anniversary edition.',
  38.99, 25, 'Books',
  'https://picsum.photos/seed/ThePragmaticProgrammer/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'System Design Interview Vol. 2',
  'Insider guide to distributed system design interviews.',
  29.99, 55, 'Books',
  'https://picsum.photos/seed/SystemDesignInterviewVol.2/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Pour-Over Coffee Set',
  'Hand-blown glass dripper, gooseneck kettle, and 100 filters.',
  44.99, 30, 'Home & Kitchen',
  'https://picsum.photos/seed/Pour-OverCoffeeSet/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Bamboo Cutting Board XL',
  'Extra-large, juice grooves, anti-slip feet, eco-friendly.',
  27.99, 70, 'Home & Kitchen',
  'https://picsum.photos/seed/BambooCuttingBoardXL/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Stainless Steel Water Bottle 1L',
  'Double-wall vacuum insulation, keeps cold 24h / hot 12h.',
  22.99, 120, 'Home & Kitchen',
  'https://picsum.photos/seed/StainlessSteelWaterBottle1L/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Yoga Mat 6mm Non-Slip',
  'Eco-friendly TPE material, alignment lines, carry strap included.',
  32.99, 90, 'Sports',
  'https://picsum.photos/seed/YogaMat6mmNon-Slip/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Adjustable Dumbbell Set 20kg',
  'Space-saving dial-select design, replaces 8 pairs of dumbbells.',
  189.99, 20, 'Sports',
  'https://picsum.photos/seed/AdjustableDumbbellSet20kg/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Resistance Bands Set (5-pack)',
  '5 resistance levels from 10 to 50 lbs, includes door anchor.',
  24.99, 150, 'Sports',
  'https://picsum.photos/seed/ResistanceBandsSet(5-pack)/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);

INSERT INTO products (name, description, price, stock, category, image_url)
SELECT * FROM (SELECT 'Jump Rope Speed Cable',
  'Adjustable 3m cable, ball-bearing handles, suitable for all ages.',
  14.99, 200, 'Sports',
  'https://picsum.photos/seed/JumpRopeSpeedCable/400/300') AS t
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = t.name);
