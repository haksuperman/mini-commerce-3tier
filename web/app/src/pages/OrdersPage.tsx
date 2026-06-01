import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listOrders } from '../api/orders';
import { getErrorMessage } from '../api/client';
import { formatDate, formatPrice } from '../lib/format';
import type { Order, OrderStatus } from '../types/api';

const statusStyles: Record<OrderStatus, string> = {
  PAID: 'bg-green-100 text-green-700',
  FAILED: 'bg-red-100 text-red-700',
  PENDING: 'bg-yellow-100 text-yellow-700',
  CANCELLED: 'bg-gray-100 text-gray-600',
};

function StatusBadge({ status }: { status: OrderStatus }) {
  const key = status.toUpperCase() as OrderStatus;
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusStyles[key] ?? ''}`}>
      {status}
    </span>
  );
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const data = await listOrders({ page: 1, page_size: 50 });
        setOrders(data.items);
      } catch (err) {
        setError(getErrorMessage(err, 'Failed to load orders'));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <p className="text-gray-500">Loading…</p>;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-gray-900">Order History</h1>

      {error && (
        <div role="alert" className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {orders.length === 0 ? (
        <div className="card p-6 text-center text-gray-500">
          <p>You have no orders yet.</p>
          <Link to="/" className="mt-2 inline-block text-indigo-600 hover:underline">
            Browse products
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div key={order.id} className="card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium text-gray-900">Order #{order.id}</span>
                  <span className="ml-2 text-sm text-gray-500">{formatDate(order.created_at)}</span>
                </div>
                <StatusBadge status={order.status} />
              </div>
              <ul className="mt-2 space-y-1 text-sm text-gray-600">
                {order.items.map((item) => (
                  <li key={item.id} className="flex justify-between">
                    <span>
                      Product #{item.product_id} × {item.quantity}
                    </span>
                    <span>{formatPrice(item.unit_price)}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-2 border-t border-gray-100 pt-2 text-right font-semibold text-gray-900">
                Total: {formatPrice(order.total_amount)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
