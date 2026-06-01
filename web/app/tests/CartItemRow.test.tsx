import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CartItemRow from '../src/components/CartItemRow';
import type { CartItem } from '../src/types/api';

const item: CartItem = {
  product_id: 7,
  quantity: 2,
  unit_price: '10.00',
  name: 'Coffee Mug',
  subtotal: '20.00',
};

describe('CartItemRow', () => {
  it('increments quantity when the + button is clicked', async () => {
    const onUpdateQty = vi.fn();
    render(
      <CartItemRow item={item} onUpdateQty={onUpdateQty} onRemove={vi.fn()} />,
    );
    await userEvent.click(screen.getByRole('button', { name: /increase quantity/i }));
    expect(onUpdateQty).toHaveBeenCalledWith(7, 3);
  });

  it('decrements quantity when the - button is clicked', async () => {
    const onUpdateQty = vi.fn();
    render(<CartItemRow item={item} onUpdateQty={onUpdateQty} onRemove={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: /decrease quantity/i }));
    expect(onUpdateQty).toHaveBeenCalledWith(7, 1);
  });

  it('calls onRemove with the product id', async () => {
    const onRemove = vi.fn();
    render(<CartItemRow item={item} onUpdateQty={vi.fn()} onRemove={onRemove} />);
    await userEvent.click(screen.getByRole('button', { name: /remove coffee mug/i }));
    expect(onRemove).toHaveBeenCalledWith(7);
  });
});
