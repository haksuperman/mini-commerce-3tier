import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import CartItemRow from '../components/CartItemRow';
import { clearCart, getCart, removeCartItem, updateCartItem } from '../api/cart';
import { getErrorMessage } from '../api/client';
import { formatPrice } from '../lib/format';
import type { CartResponse } from '../types/api';

export default function CartPage() {
  const navigate = useNavigate();
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setCart(await getCart());
      } catch (err) {
        setError(getErrorMessage(err, 'Failed to load cart'));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleUpdateQty = async (productId: number, quantity: number) => {
    setBusy(true);
    setError('');
    try {
      setCart(await updateCartItem(productId, quantity));
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update quantity'));
    } finally {
      setBusy(false);
    }
  };

  const handleRemove = async (productId: number) => {
    setBusy(true);
    setError('');
    try {
      setCart(await removeCartItem(productId));
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to remove item'));
    } finally {
      setBusy(false);
    }
  };

  const handleClear = async () => {
    setBusy(true);
    setError('');
    try {
      await clearCart();
      setCart(await getCart());
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to clear cart'));
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <p className="text-gray-500">Loading…</p>;

  const isEmpty = !cart || cart.items.length === 0;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-gray-900">Your Cart</h1>

      {error && (
        <div role="alert" className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {isEmpty ? (
        <div className="card p-6 text-center text-gray-500">
          <p>Your cart is empty.</p>
          <Link to="/" className="mt-2 inline-block text-indigo-600 hover:underline">
            Browse products
          </Link>
        </div>
      ) : (
        <div className="card p-6">
          {cart!.items.map((item) => (
            <CartItemRow
              key={item.product_id}
              item={item}
              disabled={busy}
              onUpdateQty={handleUpdateQty}
              onRemove={handleRemove}
            />
          ))}
          <div className="mt-4 flex items-center justify-between">
            <button className="btn-secondary" disabled={busy} onClick={handleClear}>
              Clear cart
            </button>
            <div className="text-right">
              <p className="text-sm text-gray-500">{cart!.item_count} item(s)</p>
              <p className="text-xl font-bold text-gray-900">Total: {formatPrice(cart!.total)}</p>
            </div>
          </div>
          <button
            className="btn-primary mt-4 w-full"
            disabled={busy}
            onClick={() => navigate('/checkout')}
          >
            Proceed to checkout
          </button>
        </div>
      )}
    </div>
  );
}
