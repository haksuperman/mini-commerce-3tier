import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProductCard from '../components/ProductCard';
import { listProducts } from '../api/products';
import { addCartItem } from '../api/cart';
import { getErrorMessage } from '../api/client';
import { useAuthStore } from '../store/authStore';
import type { Product } from '../types/api';

const PAGE_SIZE = 8;

export default function ProductListPage() {
  const navigate = useNavigate();
  const accessToken = useAuthStore((s) => s.accessToken);

  const [products, setProducts] = useState<Product[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError('');
    try {
      const data = await listProducts({ page: p, page_size: PAGE_SIZE });
      setProducts(data.items);
      setPages(data.pages);
      setPage(data.page);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load products'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(1);
  }, [load]);

  const handleAddToCart = async (product: Product) => {
    if (!accessToken) {
      navigate('/login');
      return;
    }
    setNotice('');
    try {
      await addCartItem(product.id, 1);
      setNotice(`Added "${product.name}" to cart`);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to add to cart'));
    }
  };

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-gray-900">Products</h1>

      {notice && (
        <div className="mb-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{notice}</div>
      )}
      {error && (
        <div role="alert" className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : products.length === 0 ? (
        <p className="text-gray-500">No products found.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} onAddToCart={handleAddToCart} />
          ))}
        </div>
      )}

      {pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            className="btn-secondary"
            disabled={page <= 1 || loading}
            onClick={() => load(page - 1)}
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {pages}
          </span>
          <button
            className="btn-secondary"
            disabled={page >= pages || loading}
            onClick={() => load(page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
