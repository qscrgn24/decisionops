// frontend/src/pages/about.tsx
export default function About() {
  return (
    <div className="aboutWrap">
      <div className="aboutContainer">
        <h1 className="aboutTitle">About DecisionOps</h1>

        <p className="aboutSubtitle">
          DecisionOps is an open-source tool designed to solve optimization problems using advanced
          algorithms. Built with modern web technologies, it helps teams make data-driven decisions
          by finding optimal solutions efficiently.
        </p>

        <div className="aboutCards">
          <div className="aboutCard">
            <div className="aboutCardIcon">
              {/* Rocket */}
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
                <path
                  d="M14.5 3.5c-2.9 1.2-5.7 4-6.9 6.9l-.4 1-2.4 2.4c-.5.5-.5 1.3 0 1.8l.9.9c.5.5 1.3.5 1.8 0l2.4-2.4 1-.4c2.9-1.2 5.7-4 6.9-6.9.7-1.6.8-3.3.6-4.7-1.4-.2-3.1 0-4.7.6Z"
                  stroke="rgba(255,255,255,0.75)"
                  strokeWidth="1.4"
                  strokeLinejoin="round"
                />
                <path
                  d="M8.5 15.5s-.4 2.6-2.6 4.8c2.2-.2 4.8-2.6 4.8-2.6"
                  stroke="rgba(126,96,255,0.85)"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                />
                <path
                  d="M14.8 9.2a1.6 1.6 0 1 1-2.2-2.2 1.6 1.6 0 0 1 2.2 2.2Z"
                  fill="rgba(126,96,255,0.85)"
                  opacity="0.9"
                />
              </svg>
            </div>

            <div className="aboutCardText">
              <div className="aboutCardTitle">Our Mission</div>
              <div className="aboutCardBody">
                Empowering teams to make smarter decisions through advanced optimization algorithms
                and user-friendly tools.
              </div>
            </div>
          </div>

          <div className="aboutCard">
            <div className="aboutCardIcon">
              {/* Cubes */}
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2 4 6.5V16l8 4.5 8-4.5V6.5L12 2Z"
                  stroke="rgba(255,255,255,0.75)"
                  strokeWidth="1.4"
                  strokeLinejoin="round"
                />
                <path
                  d="M12 2v9.2M4 6.5l8 4.7 8-4.7"
                  stroke="rgba(126,96,255,0.85)"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  opacity="0.95"
                />
                <path
                  d="M7.5 13.4 4 15.4M16.5 13.4 20 15.4"
                  stroke="rgba(255,255,255,0.55)"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                />
              </svg>
            </div>

            <div className="aboutCardText">
              <div className="aboutCardTitle">Technologies</div>
              <div className="aboutCardBody">
                Built with React, TypeScript, Vite, and powerful optimization libraries like Google
                OR-Tools and the CP-SAT solver.
              </div>
            </div>
          </div>

          <div className="aboutCard">
            <div className="aboutCardIcon">
              {/* Gear */}
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4Z"
                  stroke="rgba(126,96,255,0.9)"
                  strokeWidth="1.4"
                />
                <path
                  d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.4 1a7.5 7.5 0 0 0-1.7-1l-.4-2.6H9.6l-.4 2.6a7.5 7.5 0 0 0-1.7 1l-2.4-1-2 3.4 2 1.5A7 7 0 0 0 5 12c0 .3 0 .7.1 1l-2 1.5 2 3.4 2.4-1c.5.4 1.1.7 1.7 1l.4 2.6h4.8l.4-2.6c.6-.3 1.2-.6 1.7-1l2.4 1 2-3.4-2-1.5c.1-.3.1-.7.1-1Z"
                  stroke="rgba(255,255,255,0.75)"
                  strokeWidth="1.4"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            <div className="aboutCardText">
              <div className="aboutCardTitle">Get Involved</div>
              <div className="aboutCardBody">
                DecisionOps is open-source! You can contribute on GitHub, report bugs, request
                features, or discuss ideas with the community.
              </div>
            </div>
          </div>
        </div>

        <div className="aboutCtaLabel">Explore our source code and project details:</div>

        <div className="aboutCtas">
          <button className="aboutBtnGhost" type="button" onClick={() => window.open("https://github.com/qscrgn24/decisionops", "_blank")}>
            <span className="aboutBtnIcon" aria-hidden>
              {/* GitHub icon */}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2C6.5 2 2 6.6 2 12.2c0 4.5 2.9 8.3 6.9 9.6.5.1.7-.2.7-.5v-1.8c-2.8.6-3.4-1.2-3.4-1.2-.4-1.1-1.1-1.4-1.1-1.4-.9-.6.1-.6.1-.6 1 0 1.6 1 1.6 1 .9 1.6 2.4 1.1 3 .8.1-.7.4-1.1.7-1.4-2.2-.3-4.5-1.1-4.5-5a3.9 3.9 0 0 1 1-2.7c-.1-.3-.4-1.3.1-2.7 0 0 .8-.3 2.7 1a9.2 9.2 0 0 1 5 0c1.9-1.3 2.7-1 2.7-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.3 4.7-4.5 5 .4.3.7 1 .7 2v3c0 .3.2.6.7.5A10.2 10.2 0 0 0 22 12.2C22 6.6 17.5 2 12 2Z"
                  fill="rgba(255,255,255,0.8)"
                />
              </svg>
            </span>
            GitHub Repository
          </button>
        </div>

        <div className="aboutContact">
          <h3>Contact & Feedback</h3>
          <p>
            For bug reports, feature requests, or general feedback, feel free to reach out.
          </p>

          <div className="aboutContactLinks">
            <a
              href="mailto:singhaniavatsal@gmail.com"
              className="aboutContactLink"
            >
              📧 singhaniavatsal@gmail.com
            </a>

            <a
              href="https://github.com/qscrgn24/decisionops/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="aboutContactLink"
            >
              🐛 Report an issue on GitHub
            </a>
          </div>
        </div>

        <div className="aboutFooterLine" />
      </div>

      <style>{`
        .aboutWrap{
          width: 100%;
          min-height: calc(100vh - 64px);
          padding: 44px 24px 48px;
          display: flex;
          justify-content: center;
        }

        .aboutContainer{
          width: min(1100px, 100%);
          border-radius: 22px;
          padding: 44px 40px 40px;
          background: rgba(10,10,16,0.32);
          border: 1px solid rgba(255,255,255,0.08);
          box-shadow: 0 28px 90px rgba(0,0,0,0.52);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
        }

        .aboutTitle{
          text-align: center;
          margin: 0;
          font-size: 44px;
          letter-spacing: -0.02em;
        }

        .aboutSubtitle{
          text-align: center;
          margin: 16px auto 0;
          max-width: 82ch;
          color: rgba(255,255,255,0.64);
          line-height: 1.7;
          font-size: 16px;
        }

        .aboutCards{
          margin-top: 34px;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 18px;
        }

        .aboutCard{
          border-radius: 18px;
          padding: 18px 18px;
          background: rgba(8,8,14,0.45);
          border: 1px solid rgba(255,255,255,0.10);
          box-shadow: 0 18px 60px rgba(0,0,0,0.38);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          display: flex;
          gap: 14px;
          align-items: flex-start;
          min-height: 120px;
        }

        .aboutCardIcon{
          width: 52px;
          height: 52px;
          border-radius: 14px;
          display: grid;
          place-items: center;
          background: linear-gradient(180deg, rgba(126,96,255,0.16), rgba(12,11,22,0.35));
          border: 1px solid rgba(126,96,255,0.22);
          box-shadow: 0 16px 40px rgba(0,0,0,0.35);
          flex: 0 0 auto;
        }

        .aboutCardTitle{
          font-size: 18px;
          font-weight: 800;
          margin-bottom: 6px;
          color: rgba(255,255,255,0.92);
        }

        .aboutCardBody{
          color: rgba(255,255,255,0.62);
          line-height: 1.7;
          font-size: 14.5px;
        }

        .aboutCtaLabel{
          margin-top: 30px;
          text-align: center;
          color: rgba(255,255,255,0.62);
          font-size: 14px;
        }

        .aboutCtas{
          margin-top: 14px;
          display: flex;
          gap: 14px;
          justify-content: center;
          flex-wrap: wrap;
        }

        .aboutBtnGhost, .aboutBtnPrimary{
          height: 46px;
          padding: 0 16px;
          border-radius: 14px;
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(255,255,255,0.05);
          color: rgba(255,255,255,0.86);
          font-weight: 750;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 10px;
          transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
        }

        .aboutBtnPrimary{
          background: linear-gradient(180deg, rgba(126,96,255,0.85), rgba(92,66,230,0.82));
          border-color: rgba(126,96,255,0.38);
          box-shadow: 0 16px 40px rgba(74,44,220,0.25);
        }

        .aboutBtnGhost:hover, .aboutBtnPrimary:hover{
          transform: translateY(-1px);
          border-color: rgba(180,160,255,0.55);
        }

        .aboutBtnIcon{
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }

        .aboutFooterLine{
          margin-top: 28px;
          height: 1px;
          width: 100%;
          background: rgba(255,255,255,0.08);
        }

        @media (max-width: 980px){
          .aboutContainer{ padding: 36px 22px 28px; }
          .aboutCards{ grid-template-columns: 1fr; }
          .aboutTitle{ font-size: 38px; }
        }
      `}</style>
    </div>
  );
}