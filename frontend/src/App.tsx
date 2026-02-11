import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import Dashboard from "./pages/dashboard";
import About from "./pages/about";
import Navbar from "./components/navbar";
import Login from "./auth/login";
import ForgotPassword from "./auth/forgotPassword";
import RecoverUsername from "./auth/recoverUsername";
import Signup from "./auth/signup";
import RequireAuth from "./auth/requireAuth";

function NotFound() {
  return <Navigate to="/" replace />;
}

export default function App() {
  const loc = useLocation();
  const isAuthRoute = loc.pathname.startsWith("/auth");

  return (
    <div>
      {!isAuthRoute && <Navbar />}
      <Routes>
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/signup" element={<Signup />} />
        <Route path="/auth/forgot-password" element={<ForgotPassword />} />
        <Route path="/auth/recover-username" element={<RecoverUsername />} />

        <Route
          path="/"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/about"
          element={
            <RequireAuth>
              <About />
            </RequireAuth>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}