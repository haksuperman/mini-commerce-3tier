// API response/request types mirroring the FastAPI backend (Pydantic schemas).
// Note: backend serializes Decimal values as strings (e.g. "29.99").

export type UserRole = 'ADMIN' | 'USER';

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface Product {
  id: number;
  name: string;
  description: string | null;
  price: string;
  stock: number;
  category: string | null;
  image_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type ProductListResponse = Paginated<Product>;

export interface ProductCreate {
  name: string;
  description?: string | null;
  price: string;
  stock: number;
  category?: string | null;
  image_url?: string | null;
}

export interface ProductUpdate {
  name?: string;
  description?: string | null;
  price?: string;
  stock?: number;
  category?: string | null;
  image_url?: string | null;
  is_active?: boolean;
}

export interface CartItem {
  product_id: number;
  quantity: number;
  unit_price: string;
  name: string;
  subtotal: string;
}

export interface CartResponse {
  user_id: number;
  items: CartItem[];
  total: string;
  item_count: number;
}

export type OrderStatus = 'PENDING' | 'PAID' | 'FAILED' | 'CANCELLED';

export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: string;
}

export interface Order {
  id: number;
  user_id: number;
  status: OrderStatus;
  total_amount: string;
  payment_ref: string | null;
  note: string | null;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export type OrderListResponse = Paginated<Order>;
