import { Link, useNavigate } from 'react-router-dom';
import { isAdmin, useAuthStore } from '../store/authStore';
import { logout as apiLogout } from '../api/auth';

export default function Navbar() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch {
      // Stateless JWT — ignore logout errors and clear locally.
    }
    logout();
    navigate('/login');
  };

  const authed = Boolean(accessToken);

  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold text-indigo-600">
          Mini Commerce
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link to="/" className="text-gray-700 hover:text-indigo-600">
            Products
          </Link>
          {authed && (
            <>
              <Link to="/cart" className="text-gray-700 hover:text-indigo-600">
                Cart
              </Link>
              <Link to="/orders" className="text-gray-700 hover:text-indigo-600">
                Orders
              </Link>
            </>
          )}
          {authed && isAdmin(user) && (
            <Link to="/admin/products" className="font-medium text-indigo-600 hover:text-indigo-800">
              Admin
            </Link>
          )}
          {authed ? (
            <div className="flex items-center gap-3">
              <span className="text-gray-500">
                {user?.username}
                {isAdmin(user) ? ' (admin)' : ''}
              </span>
              <button onClick={handleLogout} className="btn-secondary px-3 py-1">
                Logout
              </button>
            </div>
          ) : (
            <>
              <Link to="/login" className="text-gray-700 hover:text-indigo-600">
                Login
              </Link>
              <Link to="/signup" className="btn-primary px-3 py-1">
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
