export const API = {
    async health(): Promise<{ status: string }> {
        const res = await fetch("/api/health");
        if (!res.ok) throw new Error(`health HTTP ${res.status}`);
        return res.json();
    },

    async uploadDataset(name: string, file: File) {
        const form = new FormData();
        form.append("name", name);
        form.append("file", file);

        const res = await fetch("/api/datasets/upload", {
            method: "POST",
            body: form,
        });
        if (!res.ok) throw new Error(`upload HTTP ${res.status}`);
        return res.json();
    },

    async previewDataset(datasetId: string, n: number = 10) {
        const res = await fetch(`/api/datasets/${datasetId}/preview?n=${n}`);
        if (!res.ok) throw new Error(`preview HTTP ${res.status}`);
        return res.json();
    },

    async createRun(payload: {
        dataset_id: string;
        config: {
            budget: number;
            max_items?: number | null;
            lambda_risk?: number;
            objective?: "value" | "risk_adjusted_value";
        };
    }) {
        const res = await fetch("/api/runs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`create run HTTP ${res.status}`);
        return res.json();
    },

    async getRun(runId: string) {
        const res = await fetch(`/api/runs/${runId}`);
        if (!res.ok) throw new Error(`get run HTTP ${res.status}`);
        return res.json();
    },

    async executeGreedy(runId: string) {
        const res = await fetch(`/api/runs/${runId}/execute-greedy`, {
            method: "POST",
        });
        if (!res.ok) throw new Error(`execute greedy HTTP ${res.status}`);
        return res.json();
    },

    async executeOptimal(runId: string) {
        const res = await fetch(`/api/runs/${runId}/execute-optimal`, {
            method: "POST",
        });
        if (!res.ok) throw new Error(`execute optimal HTTP ${res.status}`);
        return res.json();
    },

    async executeAll(payload: {
        dataset_id: string;
        budget: number;
        max_items: number | null;
        objective: "value" | "risk_adjusted_value";
        lambda_risk: number;
        time_limit_seconds?: number;
    }) {
        const res = await fetch(`/api/runs/execute-all`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!res.ok) {
            const t = await res.text();
            throw new Error(t || `execute all HTTP ${res.status}`);
        }
        return res.json();
    },
};

