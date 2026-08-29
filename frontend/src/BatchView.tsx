import React, { useState, useRef, useCallback } from 'react';
import {
  UploadCloud, FileText, RotateCcw, AlertTriangle, CheckCircle2,
  XCircle, Scale, ChevronDown, Download, Loader,
} from 'lucide-react';
import axios from 'axios';
import { createCase } from './api';
import { AnalyzeResponse, CaseCreate } from './types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// ── Helpers ──────────────────────────────────────────────────────────────────

const RISK_COLOR = (score: number) =>
  score >= 65 ? '#dc2626' : score >= 35 ? '#d97706' : '#16a34a';

const CLASSIFICATION_ICON = (cls: string) => {
  if (cls === 'FAKE') return <XCircle size={14} color="#dc2626" />;
  if (cls === 'SUSPICIOUS') return <AlertTriangle size={14} color="#d97706" />;
  return <CheckCircle2 size={14} color="#16a34a" />;
};

interface BatchResult extends AnalyzeResponse {
  account_id: string;
  error?: string;
  escalated?: boolean;
}

// ── Toast (lightweight, no deps) ─────────────────────────────────────────────

interface Toast { id: number; message: string; type: 'success' | 'error' }

function ToastBar({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div style={{ position: 'fixed', bottom: '1.5rem', right: '1.5rem', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {toasts.map(t => (
        <div key={t.id} style={{
          padding: '0.7rem 1rem',
          background: t.type === 'error' ? 'rgba(220,38,38,0.95)' : 'rgba(22,163,74,0.95)',
          color: '#fff', borderRadius: '6px',
          fontSize: '0.83rem', fontWeight: 600,
          boxShadow: '0 4px 14px rgba(0,0,0,0.15)',
          minWidth: '240px', maxWidth: '360px',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          animation: 'fadeInUp 0.2s ease',
        }}>
          {t.type === 'success' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
          <span style={{ flex: 1 }}>{t.message}</span>
          <button onClick={() => onDismiss(t.id)} style={{ background: 'none', color: 'rgba(255,255,255,0.7)', fontSize: '1rem', lineHeight: 1 }}>×</button>
        </div>
      ))}
    </div>
  );
}

// ── Drop Zone ────────────────────────────────────────────────────────────────

function DropZone({ onFile }: { onFile: (f: File) => void }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) onFile(file);
  };

  return (
    <div
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      style={{
        border: `2px dashed ${dragging ? 'var(--accent-gold)' : 'var(--border-default)'}`,
        borderRadius: '10px',
        padding: '3rem 2rem',
        textAlign: 'center',
        cursor: 'pointer',
        background: dragging ? 'rgba(180,83,9,0.04)' : 'var(--bg-card)',
        transition: 'all 0.2s',
      }}>
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f); }}
      />
      <UploadCloud size={36} color={dragging ? 'var(--accent-gold)' : 'var(--text-muted)'} style={{ marginBottom: '0.75rem' }} />
      <div style={{ fontSize: '1rem', fontFamily: 'var(--font-serif)', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
        Drop a CSV file here, or click to browse
      </div>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
        Accepts the same column schema as <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', background: 'var(--bg-dark)', padding: '1px 5px', borderRadius: '3px' }}>demo_batch.csv</code> in the project root.<br />
        Required columns: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>followers, following, post_count</code>. Optional: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>platform, username</code>.
      </div>
    </div>
  );
}

// ── Result Row ───────────────────────────────────────────────────────────────

function ResultRow({
  result,
  idx,
  onEscalate,
  onNavigateEscalation,
}: {
  result: BatchResult;
  idx: number;
  onEscalate: (r: BatchResult) => void;
  onNavigateEscalation: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const canEscalate = !result.error && (result.classification === 'FAKE' || result.classification === 'SUSPICIOUS');

  if (result.error) {
    return (
      <tr style={{ background: idx % 2 === 0 ? 'var(--bg-panel)' : 'var(--bg-card)', borderBottom: '1px solid var(--border-subtle)' }}>
        <td colSpan={7} style={{ padding: '0.7rem 1rem', fontSize: '0.8rem', color: '#dc2626', fontFamily: 'var(--font-mono)' }}>
          ⚠ {result.account_id} — {result.error}
        </td>
      </tr>
    );
  }

  return (
    <>
      <tr
        onClick={() => setExpanded(x => !x)}
        style={{
          cursor: 'pointer',
          background: idx % 2 === 0 ? 'var(--bg-panel)' : 'var(--bg-card)',
          borderBottom: expanded ? 'none' : '1px solid var(--border-subtle)',
          transition: 'background 0.15s',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
        onMouseLeave={e => (e.currentTarget.style.background = idx % 2 === 0 ? 'var(--bg-panel)' : 'var(--bg-card)')}
      >
        <td style={{ padding: '0.7rem 1rem', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
          {result.account_id}
        </td>
        <td style={{ padding: '0.7rem 1rem' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', background: 'var(--bg-dark)', border: '1px solid var(--border-default)', borderRadius: '3px', padding: '2px 7px', color: 'var(--text-secondary)' }}>
            {result.platform === 'twitter' ? 'X / Twitter' : 'Meta'}
          </span>
        </td>
        <td style={{ padding: '0.7rem 1rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: RISK_COLOR(result.risk_score) }}>
          {result.risk_score.toFixed(2)}
        </td>
        <td style={{ padding: '0.7rem 1rem' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '5px',
            padding: '3px 9px', borderRadius: '4px', fontWeight: 700, fontSize: '0.78rem',
            fontFamily: 'var(--font-sans)', textTransform: 'uppercase',
            color: result.classification === 'FAKE' ? '#dc2626' : result.classification === 'SUSPICIOUS' ? '#d97706' : '#16a34a',
            background: result.classification === 'FAKE' ? 'rgba(220,38,38,0.09)' : result.classification === 'SUSPICIOUS' ? 'rgba(217,119,6,0.09)' : 'rgba(22,163,74,0.09)',
            border: `1px solid ${result.classification === 'FAKE' ? 'rgba(220,38,38,0.28)' : result.classification === 'SUSPICIOUS' ? 'rgba(217,119,6,0.28)' : 'rgba(22,163,74,0.28)'}`,
          }}>
            {CLASSIFICATION_ICON(result.classification)} {result.classification}
          </span>
        </td>
        <td style={{ padding: '0.7rem 1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          {(result.confidence * 100).toFixed(1)}%
        </td>
        <td style={{ padding: '0.7rem 1rem' }}>
          <ChevronDown size={15} color="var(--text-muted)" style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
        </td>
        <td style={{ padding: '0.7rem 1rem' }} onClick={e => e.stopPropagation()}>
          {canEscalate && (
            <button
              onClick={() => {
                onEscalate(result);
              }}
              disabled={result.escalated}
              style={{
                display: 'flex', alignItems: 'center', gap: '4px',
                padding: '4px 10px', borderRadius: '4px',
                border: result.escalated ? '1px solid rgba(22,163,74,0.3)' : '1px solid rgba(220,38,38,0.3)',
                background: result.escalated ? 'rgba(22,163,74,0.09)' : 'rgba(220,38,38,0.08)',
                color: result.escalated ? '#16a34a' : '#dc2626',
                fontSize: '0.72rem', fontWeight: 700,
                cursor: result.escalated ? 'default' : 'pointer',
                whiteSpace: 'nowrap',
              }}>
              {result.escalated
                ? <><CheckCircle2 size={12} /> Escalated</>
                : <><Scale size={12} /> Escalate</>}
            </button>
          )}
        </td>
      </tr>

      {/* Expanded Reasons Row */}
      {expanded && (
        <tr style={{ background: 'rgba(180,83,9,0.03)', borderBottom: '1px solid var(--border-subtle)' }}>
          <td colSpan={7} style={{ padding: '0.85rem 1.25rem 1rem 2.5rem' }}>
            <div style={{ fontSize: '0.77rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>
              SHAP Decision Attribution
            </div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {(result.reasons || []).map((r, i) => (
                <li key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', fontSize: '0.79rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  <span style={{
                    flexShrink: 0, marginTop: '1px',
                    width: '18px', height: '18px',
                    background: 'rgba(180,83,9,0.12)', border: '1px solid rgba(180,83,9,0.25)',
                    borderRadius: '3px', color: '#b45309', fontWeight: 700, fontSize: '0.65rem',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>{i + 1}</span>
                  {r}
                </li>
              ))}
            </ul>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Main BatchView ───────────────────────────────────────────────────────────

export function BatchView({ onNavigateEscalation }: { onNavigateEscalation: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [results, setResults] = useState<BatchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const loadingRef = useRef(false);

  const addToast = (message: string, type: Toast['type']) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  };

  const dismissToast = (id: number) => setToasts(prev => prev.filter(t => t.id !== id));

  const handleFile = (f: File) => {
    setFile(f);
    setResults([]);
    setError(null);
  };

  const handleAnalyze = useCallback(async () => {
    if (!file || loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axios.post<{ results: BatchResult[] }>(
        `${API_BASE}/analyze/batch/csv`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60_000 }
      );
      setResults(res.data.results);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to process CSV. Check the file format and try again.');
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [file]);

  const handleEscalate = useCallback(async (result: BatchResult) => {
    const platform: 'twitter' | 'meta' =
      result.platform === 'twitter' ? 'twitter' : 'meta';
    const payload: CaseCreate = {
      platform,
      handle: result.account_id,
      risk_score: result.risk_score,
      classification: result.classification as 'FAKE' | 'SUSPICIOUS',
      reasons: result.reasons ?? [],
    };
    try {
      await createCase(payload);
      setResults(prev =>
        prev.map(r => r.account_id === result.account_id ? { ...r, escalated: true } : r)
      );
      addToast(`@${result.account_id} escalated to Central Agency`, 'success');
    } catch (e: any) {
      addToast(e?.response?.data?.detail ?? 'Escalation failed', 'error');
    }
  }, []);

  const handleReset = () => {
    setFile(null);
    setResults([]);
    setError(null);
  };

  const escalatedCount = results.filter(r => r.escalated).length;
  const fakeCount = results.filter(r => r.classification === 'FAKE').length;
  const suspiciousCount = results.filter(r => r.classification === 'SUSPICIOUS').length;
  const realCount = results.filter(r => r.classification === 'REAL').length;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.75rem' }}>
        <div className="eyebrow">BATCH ANALYSIS ENGINE</div>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.65rem', color: 'var(--text-primary)', marginTop: '0.15rem' }}>
          CSV Batch Profile Scanner
        </h2>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.35rem', maxWidth: '580px', lineHeight: 1.6 }}>
          Upload a CSV of account telemetry to run bulk inference. Flag individual results for escalation to the Central Agency pipeline with a single click.
        </p>
      </div>

      {/* Upload Panel */}
      <div className="editorial-panel" style={{ padding: '1.75rem', marginBottom: '1.5rem' }}>
        <div className="section-header">
          <h3 className="section-title"><span className="section-num">01 /</span> Upload Telemetry CSV</h3>
        </div>

        {!file ? (
          <DropZone onFile={handleFile} />
        ) : (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '1rem',
            padding: '1rem 1.25rem',
            background: 'rgba(180,83,9,0.06)',
            border: '1px solid rgba(180,83,9,0.2)',
            borderRadius: '8px',
          }}>
            <FileText size={24} color="#b45309" />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)' }}>{file.name}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</div>
            </div>
            <button
              onClick={handleReset}
              style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.4rem 0.75rem', border: '1px solid var(--border-default)', background: 'var(--bg-card)', borderRadius: '5px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <RotateCcw size={13} /> Change
            </button>
          </div>
        )}

        {error && (
          <div className="alert-error" style={{ marginTop: '1rem', marginBottom: 0 }}>
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={!file || loading}
            style={{ flex: 1, marginTop: 0 }}>
            {loading
              ? <><div className="spinner" /> Analyzing batch…</>
              : <><Loader size={16} /> Run Batch Analysis</>}
          </button>

          {results.length > 0 && (
            <button
              onClick={handleReset}
              className="analyze-btn"
              style={{ width: 'auto', marginTop: 0, background: 'var(--bg-card)', border: '1px solid var(--border-default)', color: 'var(--text-secondary)' }}>
              <RotateCcw size={15} /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div>
          {/* Summary Strip */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.85rem', marginBottom: '1.25rem' }}>
            {[
              { label: 'Total Scanned', value: results.length, color: '#b45309' },
              { label: 'Fake', value: fakeCount, color: '#dc2626' },
              { label: 'Suspicious', value: suspiciousCount, color: '#d97706' },
              { label: 'Escalated', value: escalatedCount, color: '#6366f1' },
            ].map(s => (
              <div key={s.label} style={{
                background: 'var(--bg-panel)', border: '1px solid var(--border-default)',
                borderRadius: '7px', padding: '0.9rem 1rem',
                boxShadow: '0 2px 6px rgba(28,25,23,0.04)',
              }}>
                <div style={{ fontSize: '0.67rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>{s.label}</div>
                <div style={{ fontSize: '1.5rem', fontFamily: 'var(--font-serif)', fontWeight: 700, color: s.color }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* Escalation CTA */}
          {(fakeCount + suspiciousCount > 0) && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '0.85rem 1.1rem',
              background: 'rgba(220,38,38,0.06)',
              border: '1px solid rgba(220,38,38,0.2)',
              borderRadius: '7px',
              marginBottom: '1rem',
            }}>
              <div style={{ fontSize: '0.83rem', color: '#dc2626', fontWeight: 600 }}>
                <AlertTriangle size={15} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                {fakeCount + suspiciousCount} accounts require review. Escalate flagged rows individually or navigate to the Escalation Centre.
              </div>
              <button
                onClick={onNavigateEscalation}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.4rem',
                  padding: '0.45rem 0.9rem',
                  background: '#dc2626', color: '#fff', border: 'none', borderRadius: '5px',
                  fontSize: '0.78rem', fontWeight: 700,
                  whiteSpace: 'nowrap',
                }}>
                <Scale size={14} /> Escalation Centre →
              </button>
            </div>
          )}

          {/* Table */}
          <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-default)', borderRadius: '8px', boxShadow: '0 4px 12px rgba(28,25,23,0.05)', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--bg-card)' }}>
                  {['Account ID', 'Platform', 'Risk Score', 'Classification', 'Confidence', 'Details', 'Action'].map(h => (
                    <th key={h} style={{
                      padding: '0.7rem 1rem',
                      textAlign: 'left',
                      fontSize: '0.67rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.07em',
                      color: 'var(--text-muted)',
                      borderBottom: '1px solid var(--border-default)',
                      whiteSpace: 'nowrap',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <ResultRow
                    key={r.account_id + i}
                    result={r}
                    idx={i}
                    onEscalate={handleEscalate}
                    onNavigateEscalation={onNavigateEscalation}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ToastBar toasts={toasts} onDismiss={dismissToast} />

      <style>{`
        @keyframes fadeInUp {
          from { transform: translateY(8px); opacity: 0; }
          to   { transform: translateY(0);   opacity: 1; }
        }
      `}</style>
    </div>
  );
}
