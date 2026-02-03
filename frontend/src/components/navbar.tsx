import { Link } from "react-router-dom";

export default function Navbar() {
    return (
        <nav
            style={{
                display: "flex",
                gap: 16,
                padding: "12px 24px",
                borderBottom: "1px solid #ddd",
                marginBottom: 24,
            }}
        >
            <b>DecisionOps</b>
            <Link to="/">Dashboard</Link>
            <Link to="/about">About</Link>
        </nav>
    );
}