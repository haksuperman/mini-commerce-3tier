import { useEffect, useState } from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import { getMe } from './api/auth';
import { useAuthStore } from './store/authStore';

export default function App() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const logout = useAuthStore((s) => s.logout);
  const [ready, setReady] = useState(false);

  // On first load, if we have a persisted token but no user, hydrate the
  // profile so route guards (admin) work after a page refresh.
  useEffect(() => {
    let active = true;
    (async () => {
      if (accessToken && !user) {
        try {
          const me = await getMe();
          if (active) setUser(me);
        } catch {
          if (active) logout();
        }
      }
      if (active) setReady(true);
    })();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 text-gray-400">
        Loading…
      </div>
    );
  }

  return <RouterProvider router={router} />;
}
