import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCart } from '../api/cart';
import { createOrder } from '../api/orders';
import { getErrorMessage } from '../api/client';
import { formatPrice } from '../lib/format';
import type { CartResponse, Order } from '../types/api';

export default function CheckoutPage() {
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [placing, setPlacing] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
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

  const handlePlaceOrder = async () => {
    setPlacing(true);
    setError('');
    try {
      const created = await createOrder();
      setOrder(created);
    } catch (err) {
      // Backend returns 402 when mock payment fails.
      setError(getErrorMessage(err, 'Order failed'));
    } finally {
      setPlacing(false);
    }
  };

  if (loading) return <p className="text-gray-500">Loading…</p>;

  // Order result screen
  if (order) {
    const paid = order.status.toUpperCase() === 'PAID';
    return (
      <div className="mx-auto max-w-md text-center">
        <div className="card p-8">
          <div
            className={`mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full text-3xl ${
              paid ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
            }`}
          >
            {paid ? '✓' : '✕'}
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            {paid ? 'Order placed!' : 'Payment failed'}
          </h1>
          <p className="mt-2 text-gray-500">
            Order #{order.id} · status: <span className="font-medium">{order.status}</span>
          </p>
          <p className="mt-1 text-gray-900">Total: {formatPrice(order.total_amount)}</p>
          {order.payment_ref && (
            <p className="mt-1 text-xs text-gray-400">Payment ref: {order.payment_ref}</p>
          )}
          <div className="mt-6 flex justify-center gap-3">
            <Link to="/orders" className="btn-primary">
              View orders
            </Link>
            <Link to="/" className="btn-secondary">
              Continue shopping
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isEmpty = !cart || cart.items.length === 0;

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-4 text-2xl font-bold text-gray-900">Checkout</h1>

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
            <div
              key={item.product_id}
              className="flex justify-between border-b border-gray-100 py-2 text-sm"
            >
              <span className="text-gray-700">
                {item.name} × {item.quantity}
              </span>
              <span className="font-medium text-gray-900">{formatPrice(item.subtotal)}</span>
            </div>
          ))}
          <div className="mt-4 flex justify-between text-lg font-bold text-gray-900">
            <span>Total</span>
            <span>{formatPrice(cart!.total)}</span>
          </div>
          <button
            className="btn-primary mt-6 w-full"
            disabled={placing}
            onClick={handlePlaceOrder}
          >
            {placing ? 'Processing payment…' : 'Place order'}
          </button>
        </div>
      )}
    </div>
  );
}
