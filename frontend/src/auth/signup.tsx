import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [agree, setAgree] = useState(false);

  const canSubmit = useMemo(() => {
    return (
      email.trim().length > 0 &&
      username.trim().length > 0 &&
      password.length >= 8 &&
      agree
    );
  }, [email, username, password, agree]);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Will be wired to backend: POST /auth/signup
    alert("Signup backend wiring next.");
  }

  function startOAuth(provider: "google" | "github") {
    window.location.href = `/api/auth/${provider}/login`;
  }

  return (
    <div className="authWrap">
      <div className="authCard glass-strong">
        <div className="authTop">
          <div className="authBrand">DecisionOps</div>
          <h1 className="authTitle">Create your account</h1>
          <p className="authSubtitle">
            Get started with DecisionOps in seconds
          </p>
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

          <button
            className="authBtnPrimary btn-primary"
            disabled={!canSubmit}
          >
            Create Account
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
