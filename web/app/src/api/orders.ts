import { apiClient } from './client';
import type { Order, OrderListResponse } from '../types/api';

export async function createOrder(): Promise<Order> {
  const { data } = await apiClient.post<Order>('/orders');
  return data;
}

export async function listOrders(params: {
  page?: number;
  page_size?: number;
} = {}): Promise<OrderListResponse> {
  const { data } = await apiClient.get<OrderListResponse>('/orders', { params });
  return data;
}
