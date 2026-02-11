import { Link, useLocation, useNavigate } from "react-router-dom";

function NavLink({
  to,
  label,
  active,
}: {
  to: string;
  label: string;
  active: boolean;
}) {
  return (
    <Link className={`topbar__link ${active ? "is-active" : ""}`} to={to}>
      {label}
    </Link>
  );
}

export default function Navbar() {
  const { pathname } = useLocation();
  const nav = useNavigate();

  const isDashboard = pathname === "/" || pathname.startsWith("/dashboard");
  const isAbout = pathname.startsWith("/about");

  async function onLogout() {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      nav("/auth/login", { replace: true });
    }
  }

  return (
    <>
      <header className="topbar">
        <div className="topbar__inner">
          <div className="topbar__left">
            <Link to="/" className="topbar__brand">
              <span className="topbar__dot" aria-hidden="true" />
              <span className="topbar__brandText">DecisionOps</span>
              <span className="topbar__beta">beta</span>
            </Link>

            <nav className="topbar__nav" aria-label="Primary">
              <NavLink to="/" label="Dashboard" active={isDashboard} />
              <NavLink to="/about" label="About" active={isAbout} />
            </nav>
          </div>

          <div className="topbar__right">
            <button className="topbar__btn" onClick={onLogout}>
              Logout
            </button>
          </div>
        </div>
      </header>

      <style>{`
        .topbar {
          position: sticky;
          top: 0;
          z-index: 50;
          width: 100%;
          border-bottom: 1px solid rgba(255,255,255,0.10);

          background: linear-gradient(
            180deg,
            rgba(18, 18, 28, 0.78),
            rgba(10, 10, 18, 0.62)
          );

          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
        }

        /* FULL-WIDTH CONTENT (no centered max-width box) */
        .topbar__inner {
          width: 100%;
          height: 64px;
          padding: 0 16px; /* small global gutter so it doesn't touch screen edge */
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
        }

        .topbar__left {
          display: flex;
          align-items: center;
          gap: 26px;
          min-width: 0;
        }

        .topbar__brand {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 8px 10px;
          border-radius: 14px;
        }

        .topbar__brand:hover {
          background: rgba(255,255,255,0.03);
        }

        .topbar__dot {
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: radial-gradient(circle at 30% 30%, rgba(167,139,250,0.95), rgba(124,92,255,0.85));
          box-shadow: 0 0 18px rgba(124, 92, 255, 0.55);
          flex: 0 0 auto;
        }

        .topbar__brandText {
          font-weight: 760;
          letter-spacing: 0.2px;
          font-size: 22px;
          color: rgba(255,255,255,0.92);
        }

        .topbar__beta {
          margin-left: 2px;
          font-size: 12px;
          padding: 4px 10px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.04);
          color: rgba(255,255,255,0.70);
          transform: translateY(-1px);
        }

        .topbar__nav {
          display: flex;
          align-items: center;
          gap: 18px;
        }

        .topbar__link {
          color: rgba(255,255,255,0.62);
          font-size: 16px;
          padding: 10px 6px;
          border-radius: 10px;
          transition: color 120ms ease, background 120ms ease;
        }

        .topbar__link:hover {
          color: rgba(255,255,255,0.82);
          background: rgba(255,255,255,0.03);
        }

        .topbar__link.is-active {
          color: rgba(255,255,255,0.88);
        }

        .topbar__right {
          display: flex;
          align-items: center;
          gap: 10px;
          flex: 0 0 auto;
        }

        .topbar__btn {
          appearance: none;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(255,255,255,0.03);
          color: rgba(255,255,255,0.80);
          padding: 9px 12px;
          border-radius: 12px;
          font-size: 14px;
          cursor: pointer;
          transition: color 120ms ease, background 120ms ease, border-color 120ms ease;
        }

        .topbar__btn:hover {
          color: rgba(255,255,255,0.92);
          background: rgba(255,255,255,0.06);
          border-color: rgba(255,255,255,0.14);
        }
      `}</style>
    </>
  );
}
