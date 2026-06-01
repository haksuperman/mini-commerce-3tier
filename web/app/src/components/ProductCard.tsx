import { Link } from 'react-router-dom';
import type { Product } from '../types/api';
import { formatPrice } from '../lib/format';

interface ProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
}

export default function ProductCard({ product, onAddToCart }: ProductCardProps) {
  const outOfStock = product.stock <= 0;

  return (
    <div className="card flex flex-col overflow-hidden">
      <Link to={`/products/${product.id}`} className="block">
        <div className="flex h-40 items-center justify-center bg-gray-100">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-sm text-gray-400">No image</span>
          )}
        </div>
      </Link>
      <div className="flex flex-1 flex-col p-4">
        {product.category && (
          <span className="mb-1 text-xs uppercase tracking-wide text-gray-400">
            {product.category}
          </span>
        )}
        <Link to={`/products/${product.id}`} className="font-medium text-gray-900 hover:text-indigo-600">
          {product.name}
        </Link>
        <div className="mt-1 flex items-center justify-between">
          <span className="text-lg font-semibold text-gray-900">{formatPrice(product.price)}</span>
          <span className={`text-xs ${outOfStock ? 'text-red-500' : 'text-gray-500'}`}>
            {outOfStock ? 'Out of stock' : `${product.stock} in stock`}
          </span>
        </div>
        {onAddToCart && (
          <button
            className="btn-primary mt-3"
            disabled={outOfStock}
            onClick={() => onAddToCart(product)}
          >
            Add to cart
          </button>
        )}
      </div>
    </div>
  );
}
