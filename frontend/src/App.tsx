import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { PanelIcon } from "./components/Icons";
import { Sidebar } from "./components/Sidebar";
import { ChatsProvider } from "./lib/ChatsContext";
import { ChatPage } from "./pages/ChatPage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";

const isMobile = () => matchMedia("(max-width: 760px)").matches;

/** Основной экран: сайдбар слева, содержимое справа. Только для вошедших. */
function Layout() {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(isMobile);

  useEffect(() => {
    const mq = matchMedia("(max-width: 760px)");
    const onChange = () => setCollapsed(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  if (!user) return <Navigate to="/login" replace />;

  return (
    <ChatsProvider userKey={user.email} key={user.email}>
      <div className="app">
        <Sidebar collapsed={collapsed} onCollapse={() => setCollapsed(true)} onNavigate={() => isMobile() && setCollapsed(true)} />
        {!collapsed && <div className="scrim" onClick={() => setCollapsed(true)} />}
        <main className="main">
          <div className="topbar">
            <button className="icon-btn open-sidebar" onClick={() => setCollapsed(false)} title="Показать панель">
              <PanelIcon />
            </button>
          </div>
          <Outlet />
        </main>
      </div>
    </ChatsProvider>
  );
}

function Routing() {
  const { user, loading } = useAuth();
  if (loading) return null;

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route element={<Layout />}>
        <Route path="/" element={<ChatPage />} />
        <Route path="/c/:chatId" element={<ChatPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routing />
      </BrowserRouter>
    </AuthProvider>
  );
}
