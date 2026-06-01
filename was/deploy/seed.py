#!/usr/bin/env python3
"""Seed script for the WAS tier — populates demo users + products.

Idempotent: skips rows that already exist. Reads DATABASE_URL from the
environment (or app settings). Adapted from the original
mini-commerce-app/scripts/seed.py; here `app/` lives at the repo root, so the
repo root (parent of deploy/) is added to sys.path.

Usage (from repo root, inside the venv):
    python deploy/seed.py
"""

from __future__ import annotations

import asyncio
import os
import sys

# Repo root (where the `app` package lives) = parent of this deploy/ dir.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.product import Product
from app.models.user import User, UserRole
from app.security import hash_password

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

SEED_PRODUCTS = [
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
    {"name": "Classic Cotton T-Shirt (White)", "price": "19.99", "stock": 200, "category": "Clothing",
     "description": "100% organic cotton, pre-shrunk, available in S/M/L/XL."},
    {"name": "Slim Fit Chino Pants", "price": "49.99", "stock": 80, "category": "Clothing",
     "description": "Stretch chino fabric, 5-pocket design, machine washable."},
    {"name": "Running Sneakers Pro", "price": "119.99", "stock": 45, "category": "Clothing",
     "description": "Lightweight mesh upper, responsive foam midsole, reflective accents."},
    {"name": "Hooded Fleece Jacket", "price": "79.99", "stock": 60, "category": "Clothing",
     "description": "Anti-pilling fleece, full-zip, kangaroo pocket, thumb holes."},
    {"name": "Clean Code", "price": "35.99", "stock": 40, "category": "Books",
     "description": "A handbook of agile software craftsmanship by Robert C. Martin."},
    {"name": "Designing Data-Intensive Applications", "price": "42.99", "stock": 35, "category": "Books",
     "description": "The big ideas behind reliable, scalable, and maintainable systems."},
    {"name": "The Pragmatic Programmer", "price": "38.99", "stock": 25, "category": "Books",
     "description": "Your journey to mastery — 20th anniversary edition."},
    {"name": "System Design Interview Vol. 2", "price": "29.99", "stock": 55, "category": "Books",
     "description": "Insider guide to distributed system design interviews."},
    {"name": "Pour-Over Coffee Set", "price": "44.99", "stock": 30, "category": "Home & Kitchen",
     "description": "Hand-blown glass dripper, gooseneck kettle, and 100 filters."},
    {"name": "Bamboo Cutting Board XL", "price": "27.99", "stock": 70, "category": "Home & Kitchen",
     "description": "Extra-large, juice grooves, anti-slip feet, eco-friendly."},
    {"name": "Stainless Steel Water Bottle 1L", "price": "22.99", "stock": 120, "category": "Home & Kitchen",
     "description": "Double-wall vacuum insulation, keeps cold 24h / hot 12h."},
    {"name": "Yoga Mat 6mm Non-Slip", "price": "32.99", "stock": 90, "category": "Sports",
     "description": "Eco-friendly TPE material, alignment lines, carry strap included."},
    {"name": "Adjustable Dumbbell Set 20kg", "price": "189.99", "stock": 20, "category": "Sports",
     "description": "Space-saving dial-select design, replaces 8 pairs of dumbbells."},
    {"name": "Resistance Bands Set (5-pack)", "price": "24.99", "stock": 150, "category": "Sports",
     "description": "5 resistance levels from 10 to 50 lbs, includes door anchor."},
    {"name": "Jump Rope Speed Cable", "price": "14.99", "stock": 200, "category": "Sports",
     "description": "Adjustable 3m cable, ball-bearing handles, suitable for all ages."},
]


async def seed(db_url: str) -> None:
    engine = create_async_engine(db_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        for user_data in SEED_USERS:
            existing = await session.execute(
                select(User).where(User.username == user_data["username"])
            )
            if existing.scalar_one_or_none() is not None:
                print(f"  [skip] user '{user_data['username']}' already exists")
                continue
            user = User(
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
            )
            session.add(user)
            print(f"  [+] user '{user_data['username']}' ({user_data['role']})")

        await session.flush()

        for product_data in SEED_PRODUCTS:
            existing = await session.execute(
                select(Product).where(Product.name == product_data["name"])
            )
            if existing.scalar_one_or_none() is not None:
                print(f"  [skip] product '{product_data['name']}' already exists")
                continue
            product = Product(
                name=product_data["name"],
                description=product_data.get("description"),
                price=Decimal(product_data["price"]),
                stock=product_data["stock"],
                category=product_data["category"],
                image_url=f"https://picsum.photos/seed/{product_data['name'].replace(' ', '')}/400/300",
            )
            session.add(product)
            print(f"  [+] product '{product_data['name']}'")

        await session.commit()

    await engine.dispose()


async def main() -> None:
    settings = get_settings()
    print(f"Seeding database: {settings.database_url.split('@')[-1]}")
    await seed(settings.database_url)
    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
