import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

type AuthResponse = {
  authenticated: boolean;
  user: {
    id: number;
    email: string;
    username: string;
  };
};

export default function Login() {
  const nav = useNavigate();

  const [identifier, setIdentifier] = useState(""); // username OR email
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    return identifier.trim().length > 0 && password.length > 0 && !loading;
  }, [identifier, password, loading]);

  async function onSubmit(e: any) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // ✅ required for HttpOnly cookie sessions
        body: JSON.stringify({
          identifier: identifier.trim(),
          password,
          // remember is not used by backend yet; kept for UI parity
        }),
      });

      if (!res.ok) {
        const msg = await safeErrorMessage(res);
        throw new Error(msg);
      }

      // Cookie is set by backend. Optionally confirm session:
      const meRes = await fetch("/api/auth/me", {
        method: "GET",
        credentials: "include",
      });

      if (!meRes.ok) {
        throw new Error("Logged in, but failed to validate session.");
      }

      const me: AuthResponse = await meRes.json();
      if (!me.authenticated) {
        throw new Error("Session not authenticated.");
      }

      nav("/", { replace: true });
    } catch (err: any) {
      setError(err?.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  {/*
  function startOAuth(provider: "google" | "github") {
    window.location.href = `/api/auth/${provider}/login`;
  }
  */}

  return (
    <div className="authWrap">
      <div className="authCard glass-strong">
        <div className="authTop">
          <div className="authBrand">DecisionOps</div>
          <h1 className="authTitle">Welcome back</h1>
          <p className="authSubtitle">Sign in to your account</p>
        </div>

        <form onSubmit={onSubmit} className="authForm">
          <label className="authLabel">
            <span>Username or Email</span>
            <input
              className="authInput"
              placeholder="yourname or user@example.com"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              autoComplete="username"
            />
          </label>

          <label className="authLabel">
            <span>Password</span>
            <input
              className="authInput"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>

          <div className="authRow">
            <label className="authCheck">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
              />
              <span>Remember me</span>
            </label>

            {/*
            <Link className="authLink" to="/auth/forgot-password">
              Forgot your password?
            </Link>
            */}
          </div>

          {error ? <div className="authError">{error}</div> : null}

          <button className="authBtnPrimary btn-primary" disabled={!canSubmit}>
            {loading ? "Signing in..." : "Sign In"}
          </button>

          <div className="authHint">
            Don’t have an account?{" "}
            <Link className="authLinkStrong" to="/auth/signup">
              Sign Up
            </Link>
          </div>
          
          {/*
          <div className="authDivider">
            <span />
            <em>or</em>
            <span />
          </div>

          <button
            type="button"
            className="authBtnOAuth"
            onClick={() => startOAuth("google")}
          >
            <span className="oauthIcon google">G</span>
            <span>Sign in with Google</span>
          </button>

          <button
            type="button"
            className="authBtnOAuth"
            onClick={() => startOAuth("github")}
          >
            <span className="oauthIcon github">⌁</span>
            <span>Sign in with GitHub</span>
          </button>
          */}
        </form>

        <div className="authFooter">
          <div className="authFooterLinks">
            <span>Created by</span>
            <a
              className="authLink"
              href="https://github.com/qscrgn24"
              target="_blank"
              rel="noreferrer"
            >
              Projects
            </a>
            <a
              className="authLink"
              href="https://github.com/qscrgn24/decisionops"
              target="_blank"
              rel="noreferrer"
            >
              Blog
            </a>
            <a className="authLink" href="mailto:singhaniavatsal@gmail.com">
              Char
            </a>
          </div>

          <div className="authFooterLinks">
            <a
              className="authLink"
              href="https://github.com/qscrgn24/decisionops/issues"
              target="_blank"
              rel="noreferrer"
            >
              Feedback
            </a>
          </div>
        </div>
      </div>

      <style>{`
        .authError{
          padding: 10px 12px;
          border-radius: 12px;
          border: 1px solid rgba(255, 85, 85, 0.25);
          background: rgba(255, 85, 85, 0.08);
          color: rgba(255,255,255,0.86);
          font-size: 13px;
        }
      `}</style>
    </div>
  );
}

async function safeErrorMessage(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (data?.detail) return String(data.detail);
    if (data?.message) return String(data.message);
  } catch {
    // ignore
  }
  return `Login failed (HTTP ${res.status})`;
}