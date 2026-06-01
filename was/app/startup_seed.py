"""
Startup seed module — populates the DB with demo data on first run.

Controlled by SEED_ON_START environment variable (default: false).
Safe to call multiple times — skips existing records.
Uses no_autoflush to prevent premature flush during existence checks.
"""

from __future__ import annotations

from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.user import User, UserRole
from app.security import hash_password

logger = structlog.get_logger(__name__)

SEED_USERS = [
    {
        "email": "admin@minicommerce.local",
        "username": "admin",
        "password": "Admin1234!",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
    },
    {
        "email": "alice@minicommerce.local",
        "username": "alice",
        "password": "Alice1234!",
        "full_name": "Alice Kim",
        "role": UserRole.USER,
    },
    {
        "email": "bob@minicommerce.local",
        "username": "bob",
        "password": "Bob1234!",
        "full_name": "Bob Lee",
        "role": UserRole.USER,
    },
]

SEED_PRODUCTS: list[dict] = [
    # Electronics
    {"name": "Wireless Bluetooth Headphones", "price": "89.99", "stock": 50, "category": "Electronics",
     "description": "Premium noise-cancelling wireless headphones with 30h battery life."},
    {"name": "USB-C Charging Hub 7-in-1", "price": "34.99", "stock": 100, "category": "Electronics",
     "description": "Expand your laptop ports with 4K HDMI, USB 3.0, SD card reader, and more."},
    {"name": "Mechanical Keyboard TKL", "price": "129.99", "stock": 30, "category": "Electronics",
     "description": "Tenkeyless mechanical keyboard with Cherry MX Red switches, RGB backlight."},
    {"name": "27-inch 4K Monitor", "price": "399.99", "stock": 15, "category": "Electronics",
     "description": "IPS panel, 144Hz refresh rate, HDR400 support, USB-C delivery."},
    {"name": "Portable SSD 1TB", "price": "74.99", "stock": 60, "category": "Electronics",
     "description": "Read up to 1050MB/s, shock-resistant, USB 3.2 Gen 2."},
    # Clothing
    {"name": "Classic Cotton T-Shirt", "price": "19.99", "stock": 200, "category": "Clothing",
     "description": "100% organic cotton, pre-shrunk, available in S/M/L/XL."},
    {"name": "Slim Fit Chino Pants", "price": "49.99", "stock": 80, "category": "Clothing",
     "description": "Stretch chino fabric, 5-pocket design, machine washable."},
    {"name": "Running Sneakers Pro", "price": "119.99", "stock": 45, "category": "Clothing",
     "description": "Lightweight mesh upper, responsive foam midsole, reflective accents."},
    {"name": "Hooded Fleece Jacket", "price": "79.99", "stock": 60, "category": "Clothing",
     "description": "Anti-pilling fleece, full-zip, kangaroo pocket, thumb holes."},
    # Books
    {"name": "Clean Code", "price": "35.99", "stock": 40, "category": "Books",
     "description": "A handbook of agile software craftsmanship by Robert C. Martin."},
    {"name": "Designing Data-Intensive Applications", "price": "42.99", "stock": 35, "category": "Books",
     "description": "The big ideas behind reliable, scalable, and maintainable systems."},
    {"name": "The Pragmatic Programmer", "price": "38.99", "stock": 25, "category": "Books",
     "description": "Your journey to mastery - 20th anniversary edition."},
    {"name": "System Design Interview Vol. 2", "price": "29.99", "stock": 55, "category": "Books",
     "description": "Insider guide to distributed system design interviews."},
    # Home & Kitchen
    {"name": "Pour-Over Coffee Set", "price": "44.99", "stock": 30, "category": "Home & Kitchen",
     "description": "Hand-blown glass dripper, gooseneck kettle, and 100 filters."},
    {"name": "Bamboo Cutting Board XL", "price": "27.99", "stock": 70, "category": "Home & Kitchen",
     "description": "Extra-large, juice grooves, anti-slip feet, eco-friendly."},
    {"name": "Stainless Steel Water Bottle 1L", "price": "22.99", "stock": 120, "category": "Home & Kitchen",
     "description": "Double-wall vacuum insulation, keeps cold 24h / hot 12h."},
    # Sports
    {"name": "Yoga Mat 6mm Non-Slip", "price": "32.99", "stock": 90, "category": "Sports",
     "description": "Eco-friendly TPE material, alignment lines, carry strap included."},
    {"name": "Adjustable Dumbbell Set 20kg", "price": "189.99", "stock": 20, "category": "Sports",
     "description": "Space-saving dial-select design, replaces 8 pairs of dumbbells."},
    {"name": "Resistance Bands Set (5-pack)", "price": "24.99", "stock": 150, "category": "Sports",
     "description": "5 resistance levels from 10 to 50 lbs, includes door anchor."},
    {"name": "Jump Rope Speed Cable", "price": "14.99", "stock": 200, "category": "Sports",
     "description": "Adjustable 3m cable, ball-bearing handles, suitable for all ages."},
]


async def run_seed(session: AsyncSession) -> None:
    """Insert seed data if not already present. Safe to call multiple times.

    Uses no_autoflush to prevent premature flushes during existence checks,
    and handles IntegrityError gracefully for concurrent worker scenarios.
    """
    try:
        await _do_seed(session)
    except IntegrityError:
        await session.rollback()
        logger.info("seed_skipped", reason="concurrent worker already seeded (IntegrityError)")


async def _do_seed(session: AsyncSession) -> None:
    seeded_users = 0
    seeded_products = 0

    # Use no_autoflush to prevent autoflush during SELECT checks
    # Note: no_autoflush is a regular (sync) context manager, not async
    with session.no_autoflush:
        for user_data in SEED_USERS:
            existing = (
                await session.execute(select(User).where(User.username == user_data["username"]))
            ).scalar_one_or_none()

            if existing is None:
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=hash_password(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                )
                session.add(user)
                seeded_users += 1

        await session.flush()

        for product_data in SEED_PRODUCTS:
            existing = (
                await session.execute(select(Product).where(Product.name == product_data["name"]))
            ).scalar_one_or_none()

            if existing is None:
                product = Product(
                    name=product_data["name"],
                    description=product_data.get("description"),
                    price=Decimal(product_data["price"]),
                    stock=product_data["stock"],
                    category=product_data.get("category"),
                    image_url=f"https://picsum.photos/seed/{abs(hash(product_data['name'])) % 1000}/400/300",
                )
                session.add(product)
                seeded_products += 1

    await session.commit()

    if seeded_users > 0 or seeded_products > 0:
        logger.info(
            "seed_complete",
            users_seeded=seeded_users,
            products_seeded=seeded_products,
        )
    else:
        logger.info("seed_skipped", reason="data already exists")
