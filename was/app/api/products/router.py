"""Products endpoints (public read, admin write)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import CurrentAdmin, DBSession
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: str | None = Query(None, description="Filter by category"),
) -> ProductListResponse:
    """List products with pagination. Public endpoint."""
    return await product_service.list_products(db, page=page, page_size=page_size, category=category)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: DBSession) -> ProductResponse:
    """Get a single product by ID. Public endpoint."""
    product = await product_service.get_product(db, product_id)
    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    body: ProductCreate,
    db: DBSession,
    _admin: CurrentAdmin,
) -> ProductResponse:
    """Create a new product. Admin only."""
    product = await product_service.create_product(db, body)
    return ProductResponse.model_validate(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    body: ProductUpdate,
    db: DBSession,
    _admin: CurrentAdmin,
) -> ProductResponse:
    """Update an existing product. Admin only."""
    product = await product_service.update_product(db, product_id, body)
    return ProductResponse.model_validate(product)
