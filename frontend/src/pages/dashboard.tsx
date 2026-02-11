import { useMemo, useState } from "react";
import { API } from "./../api";

type UploadResp = {
  id: string;
  name: string;
  original_filename: string;
  created_at: string;
};

type PreviewResp = {
  dataset_id: string;
  columns: string[];
  total_rows: number;
  has_category: boolean;
  has_risk: boolean;
  risk_scale: string | null;
  resolved_columns?: Record<string, string | null>;
  missing_required?: string[];
  rows: Array<Record<string, any>>;
  warnings: string[];
};

type RunResp = {
  id: string;
  dataset_id: string;
  status: string;
  config_json: any;
  result_json: any;
  error: string | null;
  created_at: string;
  updated_at: string;
};

const ITEM_COLS = ["item_id", "name", "cost", "value", "category", "risk"] as const;

function numOrNull(s: string): number | null {
  const t = s.trim();
  if (t === "") return null;
  const v = Number(t);
  return Number.isFinite(v) ? v : null;
}

function fmt2(v: any): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return v == null ? "—" : String(v);
  return n.toFixed(2);
}

function toCsvCell(v: any) {
  if (v == null) return "";
  const s = String(v);
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replaceAll('"', '""')}"`;
  }
  return s;
}

function downloadText(filename: string, text: string) {
  const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function stripExt(filename: string) {
  const i = filename.lastIndexOf(".");
  return i > 0 ? filename.slice(0, i) : filename;
}

function pickStatusLabel(optimal: any | null): "OPTIMAL" | "FEASIBLE" | null {
  const raw =
    optimal?.summary?.status ??
    "";
  const s = String(raw).toLowerCase();

  // explicit booleans (if backend ever returns them)
  if (optimal?.is_optimal === true) return "OPTIMAL";
  if (optimal?.is_feasible === true) return "FEASIBLE";

  if (s.includes("optimal")) return "OPTIMAL";
  if (s.includes("feasible")) return "FEASIBLE";
  if (s === "succeeded") return "FEASIBLE"; // fallback when solver status omitted but run succeeded
  return null;
}

export default function Dashboard() {
  // Inputs (no hardcoded dataset/budget/etc.)
  const [datasetName, setDatasetName] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [budget, setBudget] = useState("");
  const [maxItems, setMaxItems] = useState(""); // optional number input
  const [lambdaRisk, setLambdaRisk] = useState("0"); // slider 0..10
  const [objective, setObjective] = useState<"" | "value" | "risk_adjusted_value">("");
  const [timeLimitS, setTimeLimitS] = useState("5"); // default per request

  // Upload + preview
  const [uploading, setUploading] = useState(false);
  const [uploadResp, setUploadResp] = useState<UploadResp | null>(null);

  const [preview, setPreview] = useState<PreviewResp | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  // Run
  const [run, setRun] = useState<RunResp | null>(null);
  const [runningAll, setRunningAll] = useState(false);

  // Right-side view mode
  const [showCompare, setShowCompare] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const datasetId = useMemo(() => uploadResp?.id ?? "", [uploadResp]);


  async function onUpload() {
    setError(null);
    setRun(null);
    setShowCompare(false);

    if (!file) {
      setError("Please choose a CSV file.");
      return;
    }

    // Backend currently expects a dataset name; auto-fill from filename if blank.
    const finalName = datasetName.trim() !== "" ? datasetName.trim() : stripExt(file.name);

    setUploading(true);
    try {
      const resp = (await API.uploadDataset(finalName, file)) as UploadResp;
      setUploadResp(resp);

      setLoadingPreview(true);
      try {
        const p = (await API.previewDataset(resp.id, 10)) as PreviewResp;
        setPreview(p);
      } finally {
        setLoadingPreview(false);
      }
    } catch (e: any) {
      setError(e?.message ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function onRunOptimization() {
    setError(null);
    setShowCompare(false);

    if (!datasetId) return setError("Upload a dataset first.");

    const b = numOrNull(budget);
    const mi = numOrNull(maxItems);
    const lr = numOrNull(lambdaRisk);
    const tls = numOrNull(timeLimitS);

    if (b === null || b <= 0) return setError("Budget must be a positive number.");
    if (mi !== null && mi <= 0) return setError("Max items must be > 0 (or empty).");
    if (lr === null || lr < 0) return setError("Risk penalty (λ) must be >= 0.");
    if (!objective) return setError("Select an objective.");
    if (tls === null || tls <= 0) return setError("Time limit must be a positive number.");

    setRunningAll(true);
    try {
      const resp = (await API.executeAll({
        dataset_id: datasetId,
        budget: b,
        max_items: mi,
        objective,
        lambda_risk: lr,
        time_limit_s: tls,
      })) as RunResp;
      setRun(resp);
    } catch (e: any) {
      setError(e?.message ?? "Run failed");
    } finally {
      setRunningAll(false);
    }
  }

  // Results extraction
  const baseline = run?.result_json?.baseline ?? null;
  const optimal = run?.result_json?.optimal ?? null;

  const baselineItems: any[] = baseline?.selected_items ?? [];
  const baselineSummary = baseline?.summary ?? null;

  const optimalItems: any[] = optimal?.selected_items ?? [];
  const optimalSummary = optimal?.summary ?? null;

  const compareRows = useMemo(() => {
    const map = new Map<string, any>();

    function upsert(items: any[], key: "baseline" | "optimal") {
      for (const it of items || []) {
        const id = String(it.item_id ?? "");
        if (!id) continue;
        const prev = map.get(id) ?? { ...it, in_baseline: false, in_optimal: false };
        map.set(id, { ...prev, ...it, [`in_${key}`]: true });
      }
    }

    upsert(baselineItems, "baseline");
    upsert(optimalItems, "optimal");

    const rows = Array.from(map.values());
    rows.sort((a, b) => {
      const ao = a.in_optimal ? 1 : 0;
      const bo = b.in_optimal ? 1 : 0;
      if (ao !== bo) return bo - ao;
      const ab = a.in_baseline ? 1 : 0;
      const bb = b.in_baseline ? 1 : 0;
      if (ab !== bb) return bb - ab;
      return Number(b.value ?? 0) - Number(a.value ?? 0);
    });

    return rows;
  }, [baselineItems, optimalItems]);

  const canShowResults = run && run.status === "succeeded" && (optimal || baseline);
  const canCompare = canShowResults && baseline && optimal;
  const statusBadge = pickStatusLabel(optimal);

  const canShowPreview = !!preview && !canShowResults;

  const previewCols = useMemo(() => {
    if (!preview?.columns?.length) return [] as string[];
    const set = new Set(preview.columns)
    const ordered = [
      ...ITEM_COLS.filter((c) => set.has(c)),
      ...preview.columns.filter((c) => !ITEM_COLS.includes(c as any)),
    ];
    return ordered.slice(0, 12);
  }, [preview]);

  function renderPreview() {
    if (!preview) return null;

    const rows = preview.rows ?? []
    const missing = preview.missing_required ?? [];
    const hasMissing = missing.length > 0;

    return (
      <div className="panel full">
        <div className="sumHead" style={{ marginBottom: 10 }}>
          <div className="sumTitleRow">
            <div className="sumTitle">Dataset Preview</div>
            <span className="badge ok">READY</span>
          </div>
          <div className="muted" style={{ marginTop: 4 }}>
            {preview.total_rows.toLocaleString()} rows · {preview.columns.length} columns
            {preview.risk_scale ? ` · risk scale: ${preview.risk_scale}` : ""}
          </div>
        </div>

        {hasMissing && (
          <div className="hint" style={{ marginBottom: 10 }}>
            <b>Warnings:</b> {preview.warnings.join(" · ")}
          </div>
        )}

        <ScrollTable columns={previewCols} rows={rows} />

        <div className="muted" style={{ marginTop: 10 }}>
          Upload complete — when you're ready, choose inputs and click <b>Run Optimization</b>.
        </div>
      </div>
    );
  }

  function downloadSelectedCsv(kind: "optimal" | "baseline") {
    const items = kind === "optimal" ? optimalItems : baselineItems;
    const headers = [...ITEM_COLS];
    const lines = [
      headers.join(","),
      ...items.map((r) => headers.map((h) => toCsvCell((r as any)[h])).join(",")),
    ];
    downloadText(`decisionops_${kind}_${run?.id ?? "run"}.csv`, lines.join("\n"));
  }

  function downloadComparisonCsv() {
    const headers = ["in_baseline", "in_optimal", ...ITEM_COLS] as const;
    const lines = [
      headers.join(","),
      ...compareRows.map((r) =>
        headers
          .map((h) => {
            const v =
              h === "in_baseline"
                ? r.in_baseline
                  ? "1"
                  : "0"
                : h === "in_optimal"
                ? r.in_optimal
                  ? "1"
                  : "0"
                : (r as any)[h];
            return toCsvCell(v);
          })
          .join(",")
      ),
    ];
    downloadText(`decisionops_comparison_${run?.id ?? "run"}.csv`, lines.join("\n"));
  }

  async function copyRunJson() {
    if (!run) return;
    const payload = {
      dataset_id: run.dataset_id,
      run_id: run.id,
      status: run.status,
      config: run.config_json,
      results: run.result_json,
      error: run.error,
    };
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
  }

  // ---------- Table (single scroll container for header+body together) ----------
  function ScrollTable({
    columns,
    rows,
    leadingCols,
  }: {
    columns: string[];
    rows: Array<Record<string, any>>;
    leadingCols?: (row: any) => React.ReactNode;
  }) {
    const template = useMemo(() => {
      const w = (c:string) => {
        switch (c) {
          case "baseline":
          case "optimal":
            return "110px";
          case "item_id":
            return "90px";
          case "name":
            return "360px";
          case "cost":
          case "value":
            return "120px";
          case "category":
            return "160px";
          case "risk":
            return "120px";
          default:
            return "160px";
        }
      };
      const base = columns.map(w);
      const lead = leadingCols ? ["56px"] : [];
      return [...lead, ...base].join(" ");
    }, [columns, leadingCols]);

    return (
      <div className="tableCard full">
        <div className="tableScroll">
          <div className="tgrid thead" style={{ gridTemplateColumns: template, width: "max-content" }}>
            {leadingCols ? <div className="cell head" /> : null}
            {columns.map((c) => (
              <div key={c} className="cell head">
                {c}
              </div>
            ))}
          </div>

          {rows.map((r, idx) => (
            <div key={idx} className="tgrid trow" style={{ gridTemplateColumns: template, width: "max-content" }}>
              {leadingCols ? <div className="cell">{leadingCols(r)}</div> : null}
              {columns.map((c) => {
                const v = r[c];
                const out =
                  c === "risk" && v != null && v !== ""
                    ? fmt2(v)
                    : v == null || v === ""
                    ? "—"
                    : String(v);
                return (
                  <div key={c} className="cell">
                    {out}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="layout">
      <aside className="side">
        <div className="sideHead">
          <div className="sideTitle">Inputs</div>
          <div className="sideChev">›</div>
        </div>

        <div className="sideBody">
          <div className="blk">
            <div className="lbl">Dataset name (optional)</div>
            <input
              className="field"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="e.g., Q1 roadmap"
            />

            <div className="row2">
              <input
                className="file"
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <button className="btn" onClick={onUpload} disabled={uploading || !file}>
                {uploading ? "Uploading…" : uploadResp ? "Replace" : "Upload"}
              </button>
            </div>

            {uploadResp && (
              <div className="meta">
                <div className="muted">{uploadResp.original_filename}</div>
                <div className="muted">
                  Uploaded on {new Date(uploadResp.created_at).toLocaleDateString()}
                </div>
              </div>
            )}

            {(loadingPreview || preview?.warnings?.length) && (
              <div className="hint muted">
                {loadingPreview ? "Validating…" : `Warnings: ${preview?.warnings?.join(" · ")}`}
              </div>
            )}
          </div>

          <div className="divider" />

          <div className="blk">
            <div className="lbl">Budget</div>
            <input
              className="field"
              type="number"
              min={0}
              step="1"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="e.g., 300"
            />

            <div className="lbl" style={{ marginTop: 12 }}>
              Max items (optional)
            </div>
            <input
              className="field"
              type="number"
              min={1}
              step="1"
              value={maxItems}
              onChange={(e) => setMaxItems(e.target.value)}
              placeholder="leave blank for no limit"
            />

            <div className="lbl" style={{ marginTop: 12 }}>
              Risk penalty (λ)
            </div>
            <div className="lambdaRow">
              <input
                className="range"
                type="range"
                min="0"
                max="10"
                step="0.1"
                value={lambdaRisk}
                onChange={(e) => setLambdaRisk(e.target.value)}
              />
              <input
                className="lambdaNum"
                type="number"
                min={0}
                max={10}
                step={0.1}
                value={lambdaRisk}
                onChange={(e) => setLambdaRisk(e.target.value)}
              />
            </div>
            <div className="hint muted">0 = ignore risk. Higher values penalize risky items more.</div>

            <div className="lbl" style={{ marginTop: 12 }}>
              Objective
            </div>
            <select
              className="field select"
              value={objective}
              onChange={(e) => setObjective(e.target.value as any)}
            >
              <option value="" disabled>
                Select objective…
              </option>
              <option value="risk_adjusted_value">risk_adjusted_value</option>
              <option value="value">value</option>
            </select>

            <div className="lbl" style={{ marginTop: 12 }}>
              Time limit (seconds)
            </div>
            <input
              className="field"
              type="number"
              min={1}
              step="1"
              value={timeLimitS}
              onChange={(e) => setTimeLimitS(e.target.value)}
              placeholder="5"
            />
            <div className="hint muted">
              Start at <b>5s</b>. If status shows <b>FEASIBLE</b>, increase incrementally until it becomes <b>OPTIMAL</b>.
            </div>

            <button className="run btnPrimary" onClick={onRunOptimization} disabled={!datasetId || runningAll}>
              {runningAll ? "Running Optimization…" : "Run Optimization"}
            </button>
          </div>
        </div>
      </aside>

      <main className="main">
        <div className="inner">
          {error && (
            <div className="panel err full">
              <b>Error:</b> {error}
            </div>
          )}

          <div className="resultsTitle">Results</div>

          {!canShowResults && (
            <>
              { canShowPreview ? (
                renderPreview()
              ) : (
                <div className="panel empty full">
                  <div className="emptyTitle">No results yet</div>
                  <div className="muted">
                    Upload a dataset and click <b>Run Optimization</b>.
                  </div>
                </div>
              )}
            </>
          )}

          {canShowResults && (
            <>
              <div className="panelGlow glowStrong full">
                <div className="sumHead">
                  <div className="sumTitleRow">
                    <div className="sumTitle">Optimal (CP-SAT)</div>
                    {statusBadge && (
                      <span className={`badge ${statusBadge === "OPTIMAL" ? "ok" : "warn"}`}>
                        {statusBadge}
                      </span>
                    )}
                  </div>

                  <div className="sumActions">
                    <button className="btnGhost" onClick={() => downloadSelectedCsv("optimal")} disabled={!optimalItems.length}>
                      Download CSV
                    </button>
                    <button className="btnGhost" onClick={copyRunJson} disabled={!run}>
                      Copy JSON
                    </button>
                  </div>
                </div>

                <div className="sumMeta">
                  <span className="muted">
                    Selected: <b>{optimalSummary?.selected_count ?? "—"}</b>
                  </span>
                  <span className="muted">
                    Total cost: <b>{optimalSummary?.total_cost ?? "—"}</b>
                  </span>
                  <span className="muted">
                    Total value: <b>{optimalSummary?.total_value ?? "—"}</b>
                  </span>
                  <span className="muted">
                    Total risk: <b>{fmt2(optimalSummary?.total_risk ?? "—")}</b>
                  </span>
                </div>

                <div className="sumRow">
                  <button className="btnPrimary2" onClick={() => setShowCompare(true)} disabled={!canCompare}>
                    Compare with Baseline
                  </button>
                  {showCompare && (
                    <button className="btnGhost" onClick={() => setShowCompare(false)}>
                      View Optimal only
                    </button>
                  )}
                </div>
              </div>

              {!showCompare && (
                <ScrollTable
                  columns={[...ITEM_COLS]}
                  rows={optimalItems}
                  leadingCols={() => <span className="tick on">✓</span>}
                />
              )}

              {showCompare && (
                <>
                  <div className="panelGlow glowSoft full">
                    <div className="sumHead">
                      <div className="sumTitle">Baseline (Greedy)</div>
                      <div className="sumActions">
                        <button className="btnGhost" onClick={() => downloadSelectedCsv("baseline")} disabled={!baselineItems.length}>
                          Download CSV
                        </button>
                        <button className="btnGhost" onClick={downloadComparisonCsv} disabled={!compareRows.length}>
                          Download Comparison CSV
                        </button>
                      </div>
                    </div>

                    <div className="sumMeta">
                      <span className="muted">
                        Selected: <b>{baselineSummary?.selected_count ?? "—"}</b>
                      </span>
                      <span className="muted">
                        Total cost: <b>{baselineSummary?.total_cost ?? "—"}</b>
                      </span>
                      <span className="muted">
                        Total value: <b>{baselineSummary?.total_value ?? "—"}</b>
                      </span>
                      <span className="muted">
                        Total risk: <b>{fmt2(baselineSummary?.total_risk ?? "—")}</b>
                      </span>
                    </div>
                  </div>

                  <ScrollTable
                    columns={["baseline", "optimal", ...ITEM_COLS]}
                    rows={compareRows.map((r) => ({
                      baseline: r.in_baseline ? "✓" : "—",
                      optimal: r.in_optimal ? "✓" : "—",
                      ...r,
                    }))}
                    leadingCols={(r) => <span className={`tick ${r.optimal === "✓" ? "on" : "off"}`}>✓</span>}
                  />
                </>
              )}
            </>
          )}
        </div>
      </main>

      <style>{`
        .muted { color: rgba(255,255,255,0.58); }
        .layout { width: 100%; min-height: calc(100vh - 64px); }
        .full { width: 100%; }

        /* Sidebar */
        .side {
          position: fixed;
          top: 64px;
          left: 0;
          bottom: 0;
          width: 340px;
          border-right: 1px solid rgba(255,255,255,0.08);
          background: linear-gradient(180deg, rgba(12,12,18,0.86), rgba(10,10,16,0.72));
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
        }

        .sideHead {
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 16px;
          border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        .sideTitle {
          font-size: 34px;
          font-weight: 760;
          letter-spacing: -0.6px;
          color: rgba(255,255,255,0.90);
        }

        .sideChev { font-size: 18px; opacity: 0.55; }

        .sideBody {
          padding: 12px 14px 14px;
          height: calc(100vh - 64px - 60px);
          overflow: auto;
        }

        .blk { margin-bottom: 12px; }

        .lbl {
          font-size: 13px;
          color: rgba(255,255,255,0.72);
          margin-bottom: 6px;
        }

        .field {
          width: 100%;
          padding: 12px 12px;
          border-radius: 14px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(255,255,255,0.03);
          color: rgba(255,255,255,0.90);
        }

        .field::placeholder { color: rgba(255,255,255,0.45); }

        .select {
          appearance: none;
          -webkit-appearance: none;
          -moz-appearance: none;
          background-color: rgba(255,255,255,0.03);
          color: rgba(255,255,255,0.90);
        }

        .select option {
          background: rgb(14,14,20);
          color: rgba(255,255,255,0.92);
        }

        .row2 {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 10px;
          margin-top: 10px;
          align-items: center;
        }

        .file {
          width: 100%;
          padding: 11px 10px;
          border-radius: 14px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(255,255,255,0.02);
          color: rgba(255,255,255,0.78);
        }

        .btn {
          padding: 12px 12px;
          border-radius: 14px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(255,255,255,0.03);
          color: rgba(255,255,255,0.86);
          white-space: nowrap;
        }
        .btn:disabled { opacity: 0.55; cursor: not-allowed; }

        .meta {
          margin-top: 10px;
          padding-top: 10px;
          border-top: 1px solid rgba(255,255,255,0.08);
          font-size: 12px;
          line-height: 1.4;
        }

        .hint { margin-top: 8px; font-size: 12px; line-height: 1.35; }

        .divider {
          height: 1px;
          background: rgba(255,255,255,0.08);
          margin: 10px 0;
        }

        .lambdaRow {
          display: grid;
          grid-template-columns: 1fr 88px;
          gap: 10px;
          align-items: center;
        }

        .range { width: 100%; }
        .lambdaNum {
          width: 100%;
          padding: 10px 10px;
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(255,255,255,0.03);
          color: rgba(255,255,255,0.90);
        }

        .run {
          width: 100%;
          margin-top: 14px;
          padding: 14px 12px;
          border-radius: 16px;
          font-weight: 700;
        }

        .btnPrimary {
          border: 1px solid rgba(124,92,255,0.55);
          background: linear-gradient(180deg, rgba(124,92,255,0.95), rgba(94,64,220,0.95));
          color: rgba(255,255,255,0.92);
        }

        /* Right side */
        .main {
          margin-left: 340px;
          min-height: calc(100vh - 64px);
          padding: 18px 18px 48px;
        }

        .inner { width: 100%; max-width: none; }

        .resultsTitle {
          font-size: 54px;
          font-weight: 780;
          letter-spacing: -1px;
          margin: 6px 0 18px;
          color: rgba(255,255,255,0.92);
        }

        .panel {
          border-radius: 22px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(16,16,24,0.55);
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          box-shadow: 0 18px 70px rgba(0,0,0,0.35);
        }

        .panelGlow {
          border-radius: 22px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(16,16,24,0.55);
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          padding: 16px;
          margin-bottom: 12px;
        }

        .glowStrong {
          border-color: rgba(124,92,255,0.22);
          box-shadow: 0 18px 90px rgba(124,92,255,0.14), 0 18px 70px rgba(0,0,0,0.35);
          background: linear-gradient(90deg, rgba(124,92,255,0.18), rgba(16,16,24,0.55));
        }

        .glowSoft {
          border-color: rgba(124,92,255,0.18);
          box-shadow: 0 14px 70px rgba(124,92,255,0.10), 0 18px 70px rgba(0,0,0,0.35);
        }

        .err { padding: 12px 14px; border-color: rgba(255,120,120,0.25); margin-bottom: 14px; }
        .empty { padding: 18px; }
        .emptyTitle { font-weight: 700; margin-bottom: 6px; color: rgba(255,255,255,0.90); }

        .sumHead { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
        .sumTitle { font-size: 22px; font-weight: 780; color: rgba(255,255,255,0.94); }
        .sumTitleRow { display: flex; align-items: center; gap: 10px; }

        .badge {
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 0.6px;
          padding: 6px 10px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.04);
          color: rgba(255,255,255,0.80);
        }
        .badge.ok { border-color: rgba(120,255,180,0.22); background: rgba(120,255,180,0.08); }
        .badge.warn { border-color: rgba(255,210,120,0.22); background: rgba(255,210,120,0.08); }

        .sumActions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }

        .btnGhost {
          padding: 12px 14px;
          border-radius: 16px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(255,255,255,0.03);
          color: rgba(255,255,255,0.86);
        }

        .sumMeta { display: flex; gap: 18px; flex-wrap: wrap; margin-top: 10px; }
        .sumRow { display: flex; gap: 10px; align-items: center; margin-top: 14px; flex-wrap: wrap; }

        .btnPrimary2 {
          padding: 12px 16px;
          border-radius: 16px;
          font-weight: 700;
          border: 1px solid rgba(124,92,255,0.55);
          background: linear-gradient(180deg, rgba(124,92,255,0.95), rgba(94,64,220,0.95));
          color: rgba(255,255,255,0.92);
        }

        /* Table card + single scroll container (headers + body move together) */
        .tableCard {
          border-radius: 22px;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(16,16,24,0.55);
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          box-shadow: 0 18px 70px rgba(0,0,0,0.35);
          overflow: hidden;
        }

        .tableScroll {
          overflow: auto;
          max-height: 560px;
        }

        .tgrid { display: grid; align-items: center; width: max-content; }

        .thead {
          position: sticky;
          top: 0;
          z-index: 2;
          background: rgba(14,14,22,0.95);
          border-bottom: 1px solid rgba(255,255,255,0.10);
        }

        .trow {
          border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        .trow:hover { background: rgba(255,255,255,0.02); }

        .cell {
          padding: 14px 12px;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: rgba(255,255,255,0.86);
          border-right: 1px solid rgba(255,255,255,0.06); /* vertical grid lines */
        }
        .tgrid .cell:last-child { border-right: none; }

        .cell.head {
          color: rgba(255,255,255,0.62);
          font-size: 13px;
          font-weight: 650;
        }

        .tick {
          display: inline-flex;
          width: 24px;
          height: 24px;
          border-radius: 9px;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(255,255,255,0.02);
          color: rgba(255,255,255,0.75);
        }
        .tick.on { background: rgba(124,92,255,0.22); border-color: rgba(124,92,255,0.35); color: rgba(255,255,255,0.92); }
        .tick.off { opacity: 0.45; }

        @media (max-width: 980px) {
          .side { position: relative; top: 0; width: 100%; height: auto; }
          .sideBody { height: auto; overflow: visible; }
          .main { margin-left: 0; }
        }
      `}</style>
    </div>
  );
}
