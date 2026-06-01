import { apiClient } from './client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types/api';

export async function register(body: RegisterRequest): Promise<User> {
  const { data } = await apiClient.post<User>('/auth/register', body);
  return data;
}

export async function login(body: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', body);
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>('/auth/me');
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout');
}
