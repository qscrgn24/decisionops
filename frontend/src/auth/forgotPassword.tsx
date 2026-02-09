import { useState } from "react";
import { Link } from "react-router-dom";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Will be wired to backend: POST /auth/password/reset
    alert("Password reset email will be sent (backend wiring next).");
  }

  return (
    <div className="authWrap">
      <div className="authCard glass-strong">
        <div className="authTop">
          <div className="authBrand">DecisionOps</div>
          <h1 className="authTitle">Recover your account</h1>
          <p className="authSubtitle">
            Enter your email to reset your password.
          </p>
        </div>

        <div className="authInlineCard">
          <span>Remember your username?</span>
          <Link className="authLinkStrong" to="/auth/recover-username">
            Recover your username
          </Link>
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

          <button
            className="authBtnPrimary btn-primary"
            disabled={!email.trim()}
          >
            Send Reset Link
          </button>
        </form>

        <div className="authHint">
          Remember your password?{" "}
          <Link className="authLinkStrong" to="/auth/login">
            Sign In
          </Link>
        </div>

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

      <style>{`
        .authInlineCard {
          display:flex;
          align-items:center;
          justify-content:space-between;
          gap: 12px;
          padding: 14px 14px;
          margin: 14px 0 10px;
          border-radius: 14px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.10);
          color: rgba(255,255,255,0.70);
          font-size: 14px;
        }
      `}</style>
    </div>
  );
}
