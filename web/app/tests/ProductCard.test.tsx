import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ProductCard from '../src/components/ProductCard';
import type { Product } from '../src/types/api';

const product: Product = {
  id: 1,
  name: 'Test Widget',
  description: 'A nice widget',
  price: '29.99',
  stock: 5,
  category: 'gadgets',
  image_url: null,
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

function renderCard(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ProductCard', () => {
  it('renders product name, price and stock', () => {
    renderCard(<ProductCard product={product} />);
    expect(screen.getByText('Test Widget')).toBeInTheDocument();
    expect(screen.getByText('$29.99')).toBeInTheDocument();
    expect(screen.getByText('5 in stock')).toBeInTheDocument();
  });

  it('calls onAddToCart when the button is clicked', async () => {
    const onAddToCart = vi.fn();
    renderCard(<ProductCard product={product} onAddToCart={onAddToCart} />);
    await userEvent.click(screen.getByRole('button', { name: /add to cart/i }));
    expect(onAddToCart).toHaveBeenCalledWith(product);
  });

  it('disables add-to-cart when out of stock', () => {
    const onAddToCart = vi.fn();
    renderCard(<ProductCard product={{ ...product, stock: 0 }} onAddToCart={onAddToCart} />);
    expect(screen.getByText('Out of stock')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add to cart/i })).toBeDisabled();
  });
});
