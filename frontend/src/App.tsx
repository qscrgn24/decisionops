import { useMemo, useState } from "react";
import { API } from "./api";

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

function numOrNull(s: string): number | null {
  const t = s.trim();
  if (t === "") return null;
  const v = Number(t);
  return Number.isFinite(v) ? v : null;
}

export default function App() {
  // Upload + preview
  const [name, setName] = useState("Demo Dataset");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResp, setUploadResp] = useState<UploadResp | null>(null);

  const [preview, setPreview] = useState<PreviewResp | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  // Run config
  const [budget, setBudget] = useState("300");
  const [maxItems, setMaxItems] = useState("4");
  const [lambdaRisk, setLambdaRisk] = useState("0.3");
  const [objective, setObjective] = useState<"value" | "risk_adjusted_value">(
    "risk_adjusted_value"
  );

  const [run, setRun] = useState<RunResp | null>(null);
  const [creatingRun, setCreatingRun] = useState(false);
  const [executing, setExecuting] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const datasetId = useMemo(() => uploadResp?.id ?? "", [uploadResp]);

  async function onUpload() {
    setError(null);
    setPreview(null);
    setRun(null);
    if (!file) {
      setError("Please choose a CSV file.");
      return;
    }
    setUploading(true);
    try {
      const resp = (await API.uploadDataset(name, file)) as UploadResp;
      setUploadResp(resp);
    } catch (e: any) {
      setError(e?.message ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function onPreview() {
    setError(null);
    if (!datasetId) {
      setError("No dataset_id yet. Upload a dataset first.");
      return;
    }
    setLoadingPreview(true);
    try {
      const resp = (await API.previewDataset(datasetId, 10)) as PreviewResp;
      setPreview(resp);
    } catch (e: any) {
      setError(e?.message ?? "Preview failed");
    } finally {
      setLoadingPreview(false);
    }
  }

  async function onCreateRun() {
    setError(null);
    if (!datasetId) {
      setError("Upload a dataset first.");
      return;
    }

    const b = numOrNull(budget);
    if (b === null || b <= 0) {
      setError("Budget must be a positive number.");
      return;
    }

    const mi = numOrNull(maxItems);
    if (mi !== null && mi <= 0) {
      setError("max_items must be > 0 (or empty).");
      return;
    }

    const lr = numOrNull(lambdaRisk);
    if (lr === null || lr < 0) {
      setError("lambda_risk must be >= 0.");
      return;
    }

    setCreatingRun(true);
    try {
      const resp = (await API.createRun({
        dataset_id: datasetId,
        config: {
          budget: b,
          max_items: mi,
          lambda_risk: lr,
          objective,
        },
      })) as RunResp;
      setRun(resp);
    } catch (e: any) {
      setError(e?.message ?? "Create run failed");
    } finally {
      setCreatingRun(false);
    }
  }

  async function onExecuteGreedy() {
    setError(null);
    if (!run?.id) {
      setError("Create a run first.");
      return;
    }
    setExecuting(true);
    try {
      const resp = (await API.executeGreedy(run.id)) as RunResp;
      setRun(resp);
    } catch (e: any) {
      setError(e?.message ?? "Execute greedy failed");
    } finally {
      setExecuting(false);
    }
  }

  const baseline = run?.result_json?.baseline ?? null;
  const selectedItems: any[] = baseline?.selected_items ?? [];
  const summary = baseline?.summary ?? null;

  return (
    <div style={{ fontFamily: "system-ui", padding: 24, maxWidth: 1100 }}>
      <h1 style={{ marginBottom: 4 }}>DecisionOps</h1>
      <p style={{ marginTop: 0, color: "#444" }}>
        MVP: Upload → Preview → Create Run → Execute Greedy → Results
      </p>

      {error && (
        <div style={{ padding: 12, border: "1px solid #ccc", marginBottom: 16 }}>
          <b>Error:</b> {error}
        </div>
      )}

      {/* Upload */}
      <div
        style={{
          display: "grid",
          gap: 12,
          padding: 16,
          border: "1px solid #ddd",
          borderRadius: 8,
          marginBottom: 16,
        }}
      >
        <h2 style={{ margin: 0 }}>1) Upload</h2>

        <label>
          Dataset name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
          />
        </label>

        <label>
          CSV file
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            style={{ display: "block", marginTop: 4 }}
          />
        </label>

        <div style={{ display: "flex", gap: 12 }}>
          <button onClick={onUpload} disabled={uploading} style={{ padding: "8px 12px" }}>
            {uploading ? "Uploading..." : "Upload"}
          </button>

          <button onClick={onPreview} disabled={!datasetId || loadingPreview} style={{ padding: "8px 12px" }}>
            {loadingPreview ? "Loading..." : "Load preview"}
          </button>
        </div>

        {uploadResp && (
          <div style={{ padding: 12, background: "#fafafa", border: "1px solid #eee" }}>
            <div><b>dataset_id:</b> {uploadResp.id}</div>
            <div><b>filename:</b> {uploadResp.original_filename}</div>
            <div><b>created_at:</b> {uploadResp.created_at}</div>
          </div>
        )}
      </div>

      {/* Preview */}
      {preview && (
        <div style={{ marginBottom: 16, padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
          <h2 style={{ marginTop: 0 }}>2) Preview</h2>

          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", color: "#333" }}>
            <div><b>Total rows:</b> {preview.total_rows}</div>
            <div>
              <b>Has risk:</b> {String(preview.has_risk)}{" "}
              {preview.risk_scale ? `(${preview.risk_scale})` : ""}
            </div>
            <div><b>Has category:</b> {String(preview.has_category)}</div>
          </div>

          {preview.warnings?.length > 0 && (
            <div style={{ marginTop: 10, padding: 12, border: "1px solid #ddd", background: "#fafafa" }}>
              <b>Warnings</b>
              <ul>
                {preview.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ marginTop: 12, overflowX: "auto", border: "1px solid #ddd", borderRadius: 8 }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {preview.columns.map((c) => (
                    <th
                      key={c}
                      style={{
                        textAlign: "left",
                        padding: 10,
                        borderBottom: "1px solid #ddd",
                        background: "#fafafa",
                      }}
                    >
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, idx) => (
                  <tr key={idx}>
                    {preview.columns.map((c) => {
                      const v = row[c];
                      return (
                        <td key={c} style={{ padding: 10, borderBottom: "1px solid #eee", color: v == null ? "#888" : "inherit" }}>
                          {v == null ? "—" : String(v)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Run config */}
      <div style={{ padding: 16, border: "1px solid #ddd", borderRadius: 8, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>3) Create Run</h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label>
            Budget
            <input value={budget} onChange={(e) => setBudget(e.target.value)} style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }} />
          </label>

          <label>
            Max items (optional)
            <input value={maxItems} onChange={(e) => setMaxItems(e.target.value)} style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }} />
          </label>

          <label>
            Lambda risk (≥ 0)
            <input value={lambdaRisk} onChange={(e) => setLambdaRisk(e.target.value)} style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }} />
          </label>

          <label>
            Objective
            <select value={objective} onChange={(e) => setObjective(e.target.value as any)} style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}>
              <option value="value">value</option>
              <option value="risk_adjusted_value">risk_adjusted_value</option>
            </select>
          </label>
        </div>

        <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
          <button onClick={onCreateRun} disabled={!datasetId || creatingRun} style={{ padding: "8px 12px" }}>
            {creatingRun ? "Creating..." : "Create Run"}
          </button>

          <button onClick={onExecuteGreedy} disabled={!run?.id || executing} style={{ padding: "8px 12px" }}>
            {executing ? "Executing..." : "Execute Greedy"}
          </button>
        </div>

        {run && (
          <div style={{ marginTop: 12, padding: 12, background: "#fafafa", border: "1px solid #eee" }}>
            <div><b>run_id:</b> {run.id}</div>
            <div><b>status:</b> {run.status}</div>
            {run.error && <div><b>error:</b> {run.error}</div>}
          </div>
        )}
      </div>

      {/* Results */}
      {run && run.status === "succeeded" && baseline && (
        <div style={{ padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
          <h2 style={{ marginTop: 0 }}>4) Results</h2>

          {summary && (
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              <div><b>Selected:</b> {summary.selected_count}</div>
              <div><b>Total cost:</b> {summary.total_cost}</div>
              <div><b>Total value:</b> {summary.total_value}</div>
              {summary.total_risk != null && <div><b>Total risk:</b> {summary.total_risk}</div>}
            </div>
          )}

          <h3 style={{ marginTop: 14 }}>Selected items</h3>

          <div style={{ overflowX: "auto", border: "1px solid #ddd", borderRadius: 8 }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["item_id", "name", "cost", "value", "category", "risk"].map((c) => (
                    <th key={c} style={{ textAlign: "left", padding: 10, borderBottom: "1px solid #ddd", background: "#fafafa" }}>
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {selectedItems.map((it, idx) => (
                  <tr key={idx}>
                    {["item_id", "name", "cost", "value", "category", "risk"].map((c) => {
                      const v = it[c];
                      return (
                        <td key={c} style={{ padding: 10, borderBottom: "1px solid #eee", color: v == null ? "#888" : "inherit" }}>
                          {v == null ? "—" : String(v)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}