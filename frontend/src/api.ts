import axios from "axios";
import { AccountFeatures, AnalyzeResponse, SessionStatus } from "./types";

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
