import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import Dashboard from "./pages/dashboard";
import About from "./pages/about";
import Navbar from "./components/navbar";

function AuthPlaceholder({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <div className="auth-wrap">
      <div className="auth-card glass-strong">
        <div className="auth-badge">Coming next</div>
        <h1 className="auth-title">{title}</h1>
        <p className="auth-subtitle">{subtitle}</p>

        <div className="auth-actions">
          <Link className="auth-btn" to="/">
            Back to Dashboard
          </Link>
          <Link className="auth-btn btn-primary" to="/signup">
            Go to Sign up
          </Link>
        </div>

        <div className="auth-note">
          Side note: after we build these pages, we’ll wire them to the backend
          (auth endpoints + protected routes).
        </div>
      </div>
    </div>
  );
}

function NotFound() {
  return <Navigate to="/" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="do-app">
        <Navbar />

        <main className="do-shell">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/about" element={<About />} />

            {/* Temporary placeholders so navbar links work right now */}
            <Route
              path="/login"
              element={
                <AuthPlaceholder
                  title="Sign in"
                  subtitle="We’ll add the full auth UI + form validation next."
                />
              }
            />
            <Route
              path="/signup"
              element={
                <AuthPlaceholder
                  title="Create your account"
                  subtitle="We’ll add the full signup UI + password rules next."
                />
              }
            />

            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>

      <style>{`
        .do-app {
          min-height: 100vh;
          width: 100%;
        }

        /* This gives the same centered “content well” as the screenshots */
        .do-shell {
          width: 100%;
          max-width: 1120px;
          margin: 0 auto;
          padding: 10px 18px 44px;
        }

        /* Auth placeholders */
        .auth-wrap {
          display: grid;
          place-items: center;
          padding: 26px 0 10px;
        }

        .auth-card {
          width: 100%;
          max-width: 560px;
          padding: 22px 20px;
        }

        .auth-badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: rgba(255,255,255,0.70);
          padding: 6px 10px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.04);
        }

        .auth-title {
          margin: 14px 0 6px;
          font-size: 26px;
          letter-spacing: -0.3px;
        }

        .auth-subtitle {
          margin: 0 0 16px;
          color: rgba(255,255,255,0.66);
          line-height: 1.45;
        }

        .auth-actions {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 10px;
        }

        .auth-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 10px 12px;
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(255,255,255,0.03);
          color: rgba(255,255,255,0.86);
          font-size: 14px;
          white-space: nowrap;
        }

        .auth-note {
          margin-top: 14px;
          padding-top: 14px;
          border-top: 1px solid rgba(255,255,255,0.10);
          color: rgba(255,255,255,0.55);
          font-size: 13px;
          line-height: 1.45;
        }
      `}</style>
    </BrowserRouter>
  );
}