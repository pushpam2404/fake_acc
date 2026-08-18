import React, { useState } from "react";
import axios from "axios";
import { Upload, FileSpreadsheet, AlertCircle } from "lucide-react";

interface BatchResult {
  account_id: string;
  risk_score?: number;
  classification?: string;
  reasons?: string[];
  error?: string;
}

export const BatchView: React.FC = () => {
  const [results, setResults] = useState<BatchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    setResults([]);

    try {
      const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000";
      const res = await axios.post(`${apiBase}/analyze/batch/csv`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 15000,
      });
      setResults(res.data.results);
    } catch (err: any) {
      console.error("Batch upload failed:", err);
      setResults([
        {
          account_id: "System Alert",
          error: err.response?.data?.detail || "Connection to backend failed or timed out.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="editorial-panel" style={{ marginTop: "2rem", padding: "1.75rem" }}>
      <div className="section-header">
        <h2 className="section-title">
          <span className="section-num">04 /</span> Central Agency Dashboard (Batch CSV Analysis)
        </h2>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.25rem" }}>
        <label className="analyze-btn" style={{ width: "auto", margin: 0, padding: "0.65rem 1.25rem", cursor: "pointer" }}>
          <Upload size={16} /> Upload Batch CSV File
          <input type="file" accept=".csv" onChange={handleUpload} disabled={loading} style={{ display: "none" }} />
        </label>
        <span className="mono" style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          {loading ? "Processing dataset batch..." : "Select demo_batch.csv to analyze multi-account logs"}
        </span>
      </div>

      {loading && (
        <div style={{ padding: "1rem", background: "var(--bg-card)", border: "1px solid var(--border-default)", borderRadius: "4px", display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--accent-gold)" }}>
          <div className="spinner" />
          <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Executing parallel XGBoost inference across dataset rows...</span>
        </div>
      )}

      {results.length > 0 && (
        <div style={{ overflowX: "auto", marginTop: "1rem" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid var(--text-primary)", textAlign: "left" }}>
                <th style={{ padding: "0.6rem", fontFamily: "var(--font-serif)" }}>Account Identifier</th>
                <th style={{ padding: "0.6rem", fontFamily: "var(--font-serif)" }}>Assessed Risk Score</th>
                <th style={{ padding: "0.6rem", fontFamily: "var(--font-serif)" }}>Classification Finding</th>
                <th style={{ padding: "0.6rem", fontFamily: "var(--font-serif)" }}>Primary SHAP Reason</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)", background: i % 2 === 0 ? "var(--bg-card)" : "transparent" }}>
                  <td className="mono" style={{ padding: "0.65rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    @{r.account_id}
                  </td>
                  <td className="mono" style={{ padding: "0.65rem", fontWeight: 700, color: r.classification === "FAKE" ? "var(--color-fake)" : r.classification === "SUSPICIOUS" ? "var(--color-suspicious)" : "var(--color-real)" }}>
                    {r.risk_score !== undefined ? `${r.risk_score.toFixed(2)}%` : "—"}
                  </td>
                  <td style={{ padding: "0.65rem" }}>
                    <span className={`risk-badge ${r.classification || ""}`} style={{ fontSize: "0.72rem", padding: "0.2rem 0.6rem" }}>
                      {r.classification ?? r.error ?? "UNKNOWN"}
                    </span>
                  </td>
                  <td style={{ padding: "0.65rem", color: "var(--text-secondary)", fontSize: "0.78rem" }}>
                    {r.reasons && r.reasons.length > 0 ? r.reasons[0] : r.error ? <span style={{ color: "var(--color-fake)" }}><AlertCircle size={14} style={{ verticalAlign: "middle", marginRight: "4px" }} />{r.error}</span> : "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
