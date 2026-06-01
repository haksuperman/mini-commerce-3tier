import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <Navbar />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-gray-200 py-3 text-center text-[11px] text-gray-400">
        v{__APP_VERSION__} · {__GIT_COMMIT__} · built {__BUILD_TIME__}
      </footer>
    </div>
  );
}
