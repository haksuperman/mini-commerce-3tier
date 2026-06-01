import { apiClient } from './client';
import type { CartResponse } from '../types/api';

export async function getCart(): Promise<CartResponse> {
  const { data } = await apiClient.get<CartResponse>('/cart');
  return data;
}

export async function addCartItem(productId: number, quantity: number): Promise<CartResponse> {
  const { data } = await apiClient.post<CartResponse>('/cart/items', {
    product_id: productId,
    quantity,
  });
  return data;
}

export async function updateCartItem(productId: number, quantity: number): Promise<CartResponse> {
  const { data } = await apiClient.put<CartResponse>(`/cart/items/${productId}`, { quantity });
  return data;
}

export async function removeCartItem(productId: number): Promise<CartResponse> {
  const { data } = await apiClient.delete<CartResponse>(`/cart/items/${productId}`);
  return data;
}

export async function clearCart(): Promise<void> {
  await apiClient.delete('/cart');
}
