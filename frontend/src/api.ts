import axios from "axios";
import { AccountFeatures, AnalyzeResponse, SessionStatus, Case, CaseSummary, CaseReport, CaseCreate, CaseStatus } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60s default — URL scan may take time
});

export async function analyzeAccount(
  features: AccountFeatures
): Promise<AnalyzeResponse> {
  const res = await api.post<AnalyzeResponse>("/analyze", features);
  return res.data;
}

export async function analyzeUrl(url: string): Promise<AnalyzeResponse> {
  const res = await api.post<AnalyzeResponse>("/analyze/url", { url });
  return res.data;
}

export async function downloadReport(
  username: string,
  features: AccountFeatures,
  prediction: AnalyzeResponse
): Promise<Blob> {
  const res = await api.post("/analyze/report", { username, features, prediction }, {
    responseType: "blob"
  });
  return res.data;
}

export async function checkHealth(): Promise<{ status: string; message: string }> {
  const res = await api.get<{ status: string; message: string }>("/health");
  return res.data;
}

// ── Session Management ──────────────────────────────────────────────────────

export async function getSessionStatus(): Promise<SessionStatus> {
  const res = await api.get<SessionStatus>("/session/status");
  return res.data;
}

export async function captureSession(
  platform: "twitter" | "instagram" | "facebook"
): Promise<{ status: string; platform: string; cookies_saved: number; message: string }> {
  // Uses a separate axios instance with a 4-minute timeout
  // (user has up to 3 minutes to log in manually in the Chromium window)
  const res = await axios.post(
    `${API_BASE}/session/capture`,
    { platform },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 240_000, // 4 minutes
    }
  );
  return res.data;
}

export async function revokeSession(
  platform: "twitter" | "instagram" | "facebook"
): Promise<{ status: string; platform: string; message: string }> {
  const res = await api.post("/session/revoke", { platform });
  return res.data;
}

// ── Case Management (Escalation Module) ─────────────────────────────────────

export async function getCases(): Promise<Case[]> {
  const res = await api.get<Case[]>("/cases");
  return res.data;
}

export async function getCaseSummary(): Promise<CaseSummary> {
  const res = await api.get<CaseSummary>("/cases/summary");
  return res.data;
}

export async function getCaseReport(id: string): Promise<CaseReport> {
  const res = await api.get<CaseReport>(`/cases/${id}/report`);
  return res.data;
}

export async function updateCaseStatus(
  id: string,
  status: CaseStatus,
  reviewed_by?: string
): Promise<Case> {
  const res = await api.patch<Case>(`/cases/${id}/status`, { status, reviewed_by });
  return res.data;
}

export async function createCase(payload: CaseCreate): Promise<Case> {
  const res = await api.post<Case>("/cases", payload);
  return res.data;
}
