import type { CartItem } from '../types/api';
import { formatPrice } from '../lib/format';

interface CartItemRowProps {
  item: CartItem;
  disabled?: boolean;
  onUpdateQty: (productId: number, quantity: number) => void;
  onRemove: (productId: number) => void;
}

export default function CartItemRow({ item, disabled, onUpdateQty, onRemove }: CartItemRowProps) {
  const decrement = () => onUpdateQty(item.product_id, Math.max(1, item.quantity - 1));
  const increment = () => onUpdateQty(item.product_id, item.quantity + 1);

  return (
    <div className="flex items-center justify-between gap-4 border-b border-gray-100 py-3">
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-gray-900">{item.name}</p>
        <p className="text-sm text-gray-500">{formatPrice(item.unit_price)} each</p>
      </div>
      <div className="flex items-center gap-2">
        <button
          aria-label="Decrease quantity"
          className="btn-secondary px-2 py-1"
          disabled={disabled || item.quantity <= 1}
          onClick={decrement}
        >
          −
        </button>
        <input
          type="number"
          min={1}
          aria-label={`Quantity for ${item.name}`}
          className="input w-16 text-center"
          value={item.quantity}
          disabled={disabled}
          onChange={(e) => {
            const next = Number(e.target.value);
            if (next >= 1) onUpdateQty(item.product_id, next);
          }}
        />
        <button
          aria-label="Increase quantity"
          className="btn-secondary px-2 py-1"
          disabled={disabled}
          onClick={increment}
        >
          +
        </button>
      </div>
      <div className="w-24 text-right font-semibold text-gray-900">{formatPrice(item.subtotal)}</div>
      <button
        aria-label={`Remove ${item.name}`}
        className="btn-danger px-3 py-1"
        disabled={disabled}
        onClick={() => onRemove(item.product_id)}
      >
        Remove
      </button>
    </div>
  );
}
