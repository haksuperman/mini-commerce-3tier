import { Navigate, Outlet } from 'react-router-dom';
import { isAdmin, useAuthStore } from '../store/authStore';

export default function AdminRoute() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }
  if (!isAdmin(user)) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
