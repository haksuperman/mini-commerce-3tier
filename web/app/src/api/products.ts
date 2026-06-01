import { apiClient } from './client';
import type {
  Product,
  ProductCreate,
  ProductListResponse,
  ProductUpdate,
} from '../types/api';

export async function listProducts(params: {
  page?: number;
  page_size?: number;
  category?: string;
} = {}): Promise<ProductListResponse> {
  const { data } = await apiClient.get<ProductListResponse>('/products', { params });
  return data;
}

export async function getProduct(id: number): Promise<Product> {
  const { data } = await apiClient.get<Product>(`/products/${id}`);
  return data;
}

export async function createProduct(body: ProductCreate): Promise<Product> {
  const { data } = await apiClient.post<Product>('/products', body);
  return data;
}

export async function updateProduct(id: number, body: ProductUpdate): Promise<Product> {
  const { data } = await apiClient.patch<Product>(`/products/${id}`, body);
  return data;
}
