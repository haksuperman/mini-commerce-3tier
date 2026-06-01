"""Product service: CRUD operations with pagination."""

from __future__ import annotations

import math

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate

logger = structlog.get_logger(__name__)


async def list_products(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    active_only: bool = True,
) -> ProductListResponse:
    """Return paginated list of products."""
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    if active_only:
        query = query.where(Product.is_active.is_(True))
        count_query = count_query.where(Product.is_active.is_(True))

    if category:
        query = query.where(Product.category == category)
        count_query = count_query.where(Product.category == category)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Product.id)
    result = await db.execute(query)
    products = list(result.scalars().all())

    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


async def get_product(db: AsyncSession, product_id: int) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise NotFoundError(f"Product {product_id} not found")
    return product


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    logger.info("product_created", product_id=product.id, name=product.name)
    return product


async def update_product(db: AsyncSession, product_id: int, data: ProductUpdate) -> Product:
    product = await get_product(db, product_id)
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(product, key, value)
    await db.flush()
    await db.refresh(product)
    logger.info("product_updated", product_id=product_id, updates=list(updates.keys()))
    return product
