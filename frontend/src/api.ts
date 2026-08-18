import axios from "axios";
import { AccountFeatures, AnalyzeResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 5000, // Hard kill switch at 5 seconds for single account requests
});

export async function analyzeAccount(
  features: AccountFeatures
): Promise<AnalyzeResponse> {
  const res = await api.post<AnalyzeResponse>("/analyze", features);
  return res.data;
}

export async function checkHealth(): Promise<{ status: string; message: string }> {
  const res = await api.get<{ status: string; message: string }>("/health");
  return res.data;
}
