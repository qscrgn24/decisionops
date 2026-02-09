import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);

  const canSubmit = useMemo(
    () => email.trim().length > 0 && password.length > 0,
    [email, password]
  );

  function onSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    // Email/password auth will be wired after OAuth
    alert("Email/password auth will be wired next.");
  }

  function startOAuth(provider: "google" | "github") {
    // Vite proxy: /api -> FastAPI backend
    window.location.href = `/api/auth/${provider}/login`;
  }

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

            <Link className="authLink" to="/auth/forgot-password">
              Forgot your password?
            </Link>
          </div>

          <button
            className="authBtnPrimary btn-primary"
            disabled={!canSubmit}
          >
            Sign In
          </button>

          <div className="authHint">
            Don’t have an account?{" "}
            <Link className="authLinkStrong" to="/auth/signup">
              Sign Up
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
            <a
              className="authLink"
              href="mailto:singhaniavatsal@gmail.com"
            >
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
    </div>
  );
}
