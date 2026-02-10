import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

type AuthMeResponse = {
  authenticated: boolean;
  user?: {
    id: number;
    email: string;
    username: string;
  };
};

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const loc = useLocation();

  const [loading, setLoading] = useState(true);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      try {
        const res = await fetch("/api/auth/me", {
          method: "GET",
          credentials: "include",
        });

        if (!res.ok) {
          if (!cancelled) {
            setAuthed(false);
            setLoading(false);
          }
          return;
        }

        const data: AuthMeResponse = await res.json();
        if (!cancelled) {
          setAuthed(!!data?.authenticated);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setAuthed(false);
          setLoading(false);
        }
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: 18 }}>
        <div className="glass-strong" style={{ padding: 16, borderRadius: 16 }}>
          Checking session…
        </div>
      </div>
    );
  }

  if (!authed) {
    // preserve where the user tried to go
    const next = encodeURIComponent(loc.pathname + loc.search);
    return <Navigate to={`/auth/login?next=${next}`} replace />;
  }

  return <>{children}</>;
}
