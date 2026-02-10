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

export default function Signup() {
  const nav = useNavigate();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [agree, setAgree] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    return (
      email.trim().length > 0 &&
      username.trim().length > 0 &&
      password.length >= 8 &&
      agree &&
      !loading
    );
  }, [email, username, password, agree, loading]);

  async function onSubmit(e: any) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // ✅ required for HttpOnly cookie sessions
        body: JSON.stringify({
          email: email.trim(),
          username: username.trim(),
          password,
        }),
      });

      if (!res.ok) {
        const msg = await safeErrorMessage(res);
        throw new Error(msg);
      }

      // Cookie is set by backend. Confirm session:
      const meRes = await fetch("/api/auth/me", {
        method: "GET",
        credentials: "include",
      });

      if (!meRes.ok) {
        throw new Error("Account created, but failed to validate session.");
      }

      const me: AuthResponse = await meRes.json();
      if (!me.authenticated) {
        throw new Error("Session not authenticated.");
      }

      nav("/", { replace: true });
    } catch (err: any) {
      setError(err?.message || "Signup failed.");
    } finally {
      setLoading(false);
    }
  }

  function startOAuth(provider: "google" | "github") {
    // OAuth endpoints will be wired later
    window.location.href = `/api/auth/${provider}/login`;
  }

  return (
    <div className="authWrap">
      <div className="authCard glass-strong">
        <div className="authTop">
          <div className="authBrand">DecisionOps</div>
          <h1 className="authTitle">Create your account</h1>
          <p className="authSubtitle">Get started with DecisionOps in seconds</p>
        </div>

        <form onSubmit={onSubmit} className="authForm">
          <label className="authLabel">
            <span>Email</span>
            <input
              className="authInput"
              placeholder="user@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </label>

          <label className="authLabel">
            <span>Username</span>
            <input
              className="authInput"
              placeholder="yourname"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </label>

          <label className="authLabel">
            <span>Password</span>
            <input
              className="authInput"
              type="password"
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
            />
          </label>

          <label className="authCheck">
            <input
              type="checkbox"
              checked={agree}
              onChange={(e) => setAgree(e.target.checked)}
            />
            <span>
              I agree to the{" "}
              <a className="authLink" href="#">
                Terms
              </a>{" "}
              and{" "}
              <a className="authLink" href="#">
                Privacy Policy
              </a>
            </span>
          </label>

          {error ? <div className="authError">{error}</div> : null}

          <button className="authBtnPrimary btn-primary" disabled={!canSubmit}>
            {loading ? "Creating..." : "Create Account"}
          </button>

          <div className="authHint">
            Already have an account?{" "}
            <Link className="authLinkStrong" to="/auth/login">
              Sign In
            </Link>
          </div>

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
            <span>Sign up with Google</span>
          </button>

          <button
            type="button"
            className="authBtnOAuth"
            onClick={() => startOAuth("github")}
          >
            <span className="oauthIcon github">⌁</span>
            <span>Sign up with GitHub</span>
          </button>
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
  return `Signup failed (HTTP ${res.status})`;
}
