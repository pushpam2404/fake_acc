import axios from "axios";
import { AccountFeatures, AnalyzeResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 seconds for live Playwright headless browser extraction
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

