import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getProduct } from '../api/products';
import { addCartItem } from '../api/cart';
import { getErrorMessage } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { formatPrice } from '../lib/format';
import type { Product } from '../types/api';

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const accessToken = useAuthStore((s) => s.accessToken);

  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    const pid = Number(id);
    if (!pid) {
      setError('Invalid product');
      setLoading(false);
      return;
    }
    (async () => {
      setLoading(true);
      try {
        setProduct(await getProduct(pid));
      } catch (err) {
        setError(getErrorMessage(err, 'Product not found'));
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleAddToCart = async () => {
    if (!product) return;
    if (!accessToken) {
      navigate('/login');
      return;
    }
    setNotice('');
    setError('');
    try {
      await addCartItem(product.id, quantity);
      setNotice(`Added ${quantity} × "${product.name}" to cart`);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to add to cart'));
    }
  };

  if (loading) return <p className="text-gray-500">Loading…</p>;
  if (error && !product)
    return (
      <div>
        <p className="mb-4 text-red-600">{error}</p>
        <Link to="/" className="text-indigo-600 hover:underline">
          Back to products
        </Link>
      </div>
    );
  if (!product) return null;

  const outOfStock = product.stock <= 0;

  return (
    <div>
      <Link to="/" className="text-sm text-indigo-600 hover:underline">
        ← Back to products
      </Link>
      <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="card flex h-72 items-center justify-center bg-gray-100">
          {product.image_url ? (
            <img src={product.image_url} alt={product.name} className="h-full w-full object-cover" />
          ) : (
            <span className="text-gray-400">No image</span>
          )}
        </div>
        <div>
          {product.category && (
            <span className="text-xs uppercase tracking-wide text-gray-400">{product.category}</span>
          )}
          <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
          <p className="mt-2 text-2xl font-semibold text-indigo-600">{formatPrice(product.price)}</p>
          <p className={`mt-1 text-sm ${outOfStock ? 'text-red-500' : 'text-gray-500'}`}>
            {outOfStock ? 'Out of stock' : `${product.stock} in stock`}
          </p>
          {product.description && <p className="mt-4 text-gray-700">{product.description}</p>}

          {notice && (
            <div className="mt-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
              {notice}
            </div>
          )}
          {error && (
            <div role="alert" className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="mt-6 flex items-center gap-3">
            <input
              type="number"
              min={1}
              max={Math.max(1, product.stock)}
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, Number(e.target.value) || 1))}
              className="input w-20"
              aria-label="Quantity"
            />
            <button className="btn-primary" disabled={outOfStock} onClick={handleAddToCart}>
              Add to cart
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
