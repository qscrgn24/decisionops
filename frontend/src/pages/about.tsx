export default function About() {
    return (
        <div style={{ maxWidth: 900, padding: 24 }}>
            <h1>About DecisionOps</h1>

            <p>
                DecisionOps is a decision optimization tool that helps teams select the
                highest-value set of initiatives under real-world constraints like
                budget, risk, and capacity.
            </p>

            <h2>How it works</h2>
            <ol>
                <li>Upload a CSV of candidate initiatives</li>
                <li>Preview and validate the data</li>
                <li>Run greedy and optimal (CP-SAT) solvers</li>
                <li>Compare results instantly</li>
            </ol>

            <h2>Contact</h2>
            <p>
                Feedback, bug reports, or ideas are welcome:
                <br />
                <b>singhaniavatsal@gmail.com</b>
            </p>
        </div>
    );
}