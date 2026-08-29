import React, { useState, useEffect, useCallback } from 'react';
import {
  Scale, RefreshCw, ChevronRight, X, FileText, Copy, Check,
  AlertTriangle, XCircle, Clock, BarChart3, BookOpen, Printer,
  Shield, TrendingUp, CheckCircle2,
} from 'lucide-react';
import {
  getCases, getCaseSummary, getCaseReport, updateCaseStatus, createCase,
} from './api';
import { Case, CaseSummary, CaseReport, CaseStatus } from './types';

// ── Status helpers ───────────────────────────────────────────────────────────

const STATUS_ORDER: CaseStatus[] = [
  'FLAGGED', 'UNDER_REVIEW', 'REPORT_SENT', 'TAKEDOWN_CONFIRMED',
];

const NEXT_STATUS: Partial<Record<CaseStatus, CaseStatus>> = {
  FLAGGED: 'UNDER_REVIEW',
  UNDER_REVIEW: 'REPORT_SENT',
  REPORT_SENT: 'TAKEDOWN_CONFIRMED',
};

const STATUS_LABELS: Record<CaseStatus, string> = {
  FLAGGED: 'Flagged',
  UNDER_REVIEW: 'Under Review',
  REPORT_SENT: 'Report Sent',
  TAKEDOWN_CONFIRMED: 'Takedown Confirmed',
};

const STATUS_COLORS: Record<CaseStatus, { color: string; bg: string; border: string }> = {
  FLAGGED:            { color: '#dc2626', bg: 'rgba(220,38,38,0.10)',   border: 'rgba(220,38,38,0.30)'   },
  UNDER_REVIEW:       { color: '#d97706', bg: 'rgba(217,119,6,0.10)',   border: 'rgba(217,119,6,0.30)'   },
  REPORT_SENT:        { color: '#6366f1', bg: 'rgba(99,102,241,0.10)',  border: 'rgba(99,102,241,0.30)'  },
  TAKEDOWN_CONFIRMED: { color: '#16a34a', bg: 'rgba(22,163,74,0.10)',   border: 'rgba(22,163,74,0.30)'   },
};

const RISK_COLOR = (score: number) =>
  score >= 65 ? '#dc2626' : score >= 35 ? '#d97706' : '#16a34a';

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

// ── Toast ────────────────────────────────────────────────────────────────────

interface Toast { id: number; message: string; type: 'success' | 'error' | 'info' }

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div style={{ position: 'fixed', bottom: '1.5rem', right: '1.5rem', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {toasts.map(t => (
        <div key={t.id} style={{
          display: 'flex', alignItems: 'center', gap: '0.65rem',
          padding: '0.75rem 1rem',
          background: t.type === 'error' ? 'rgba(220,38,38,0.95)' : t.type === 'success' ? 'rgba(22,163,74,0.95)' : 'rgba(28,25,23,0.93)',
          color: '#fff',
          borderRadius: '6px',
          fontSize: '0.83rem',
          fontFamily: 'var(--font-sans)',
          fontWeight: 600,
          boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
          minWidth: '260px',
          maxWidth: '380px',
          animation: 'fadeInUp 0.2s ease',
        }}>
          {t.type === 'success' && <CheckCircle2 size={15} />}
          {t.type === 'error' && <AlertTriangle size={15} />}
          {t.type === 'info' && <Shield size={15} />}
          <span style={{ flex: 1 }}>{t.message}</span>
          <button onClick={() => onDismiss(t.id)} style={{ background: 'none', color: 'rgba(255,255,255,0.7)', padding: '2px', borderRadius: '3px' }}>
            <X size={13} />
          </button>
        </div>
      ))}
    </div>
  );
}

// ── Status Badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: CaseStatus }) {
  const c = STATUS_COLORS[status];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '3px 9px',
      borderRadius: '4px',
      fontSize: '0.72rem',
      fontWeight: 700,
      fontFamily: 'var(--font-sans)',
      letterSpacing: '0.04em',
      textTransform: 'uppercase' as const,
      color: c.color,
      background: c.bg,
      border: `1px solid ${c.border}`,
      whiteSpace: 'nowrap' as const,
    }}>
      {status === 'FLAGGED' && <XCircle size={11} />}
      {status === 'UNDER_REVIEW' && <AlertTriangle size={11} />}
      {status === 'REPORT_SENT' && <FileText size={11} />}
      {status === 'TAKEDOWN_CONFIRMED' && <CheckCircle2 size={11} />}
      {STATUS_LABELS[status]}
    </span>
  );
}

// ── Summary Strip ────────────────────────────────────────────────────────────

function SummaryStrip({ summary, loading }: { summary: CaseSummary | null; loading: boolean }) {
  const cards = [
    {
      label: 'Total Escalated',
      value: summary?.total_flagged ?? '—',
      icon: <Scale size={20} color="#b45309" />,
      color: '#b45309',
    },
    {
      label: 'Pending Review',
      value: summary?.pending_review ?? '—',
      icon: <Clock size={20} color="#d97706" />,
      color: '#d97706',
    },
    {
      label: 'Reports Sent',
      value: summary?.reports_sent ?? '—',
      icon: <FileText size={20} color="#6366f1" />,
      color: '#6366f1',
    },
    {
      label: 'Avg. Time-to-Takedown',
      value: summary?.avg_time_to_takedown_hours != null
        ? `${summary.avg_time_to_takedown_hours.toFixed(1)}h`
        : 'N/A',
      icon: <TrendingUp size={20} color="#16a34a" />,
      color: '#16a34a',
    },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: '1rem',
      marginBottom: '1.75rem',
    }}>
      {cards.map((c, i) => (
        <div key={i} style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-default)',
          borderRadius: '8px',
          padding: '1.1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.85rem',
          boxShadow: '0 2px 8px rgba(28,25,23,0.05)',
          transition: 'box-shadow 0.2s',
        }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '8px',
            background: `${c.color}18`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>{c.icon}</div>
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2px' }}>
              {c.label}
            </div>
            <div style={{
              fontSize: loading ? '1rem' : '1.5rem',
              fontFamily: 'var(--font-serif)',
              fontWeight: 700,
              color: loading ? 'var(--text-muted)' : 'var(--text-primary)',
            }}>
              {loading ? '…' : c.value}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Report Modal ─────────────────────────────────────────────────────────────

function ReportModal({ report, onClose }: { report: CaseReport; onClose: () => void }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const statusC = STATUS_COLORS[report.status as CaseStatus] ?? STATUS_COLORS.FLAGGED;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 8000,
      background: 'rgba(28,25,23,0.55)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '1.5rem',
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-panel)',
        border: '1px solid var(--border-default)',
        borderRadius: '10px',
        width: '100%',
        maxWidth: '680px',
        maxHeight: '88vh',
        overflowY: 'auto',
        boxShadow: '0 20px 60px rgba(28,25,23,0.18)',
      }} onClick={e => e.stopPropagation()}>

        {/* Report Header */}
        <div style={{
          padding: '1.5rem 1.75rem 1rem',
          borderBottom: '2px solid var(--text-primary)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
        }}>
          <div>
            <div className="eyebrow">CENTRAL AGENCY TAKEDOWN REPORT</div>
            <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.4rem', marginTop: '0.2rem' }}>
              Formal Escalation Notice
            </h2>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem', fontFamily: 'var(--font-mono)' }}>
              Case ID: {report.case_id} &nbsp;·&nbsp; Generated: {formatDate(report.generated_at)}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
            <button
              onClick={handleCopy}
              title="Copy as JSON"
              style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.5rem 0.85rem',
                border: '1px solid var(--border-default)',
                background: 'var(--bg-card)',
                borderRadius: '5px',
                fontSize: '0.78rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
              }}>
              {copied ? <Check size={14} color="#16a34a" /> : <Copy size={14} />}
              {copied ? 'Copied!' : 'Copy JSON'}
            </button>
            <button
              onClick={() => window.print()}
              title="Print report"
              style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.5rem 0.85rem',
                border: '1px solid var(--border-default)',
                background: 'var(--bg-card)',
                borderRadius: '5px',
                fontSize: '0.78rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
              }}>
              <Printer size={14} />
              Print (Cmd+P)
            </button>
            <button onClick={onClose} style={{ padding: '0.45rem', border: '1px solid var(--border-default)', background: 'var(--bg-card)', borderRadius: '5px', color: 'var(--text-muted)' }}>
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Report Body */}
        <div style={{ padding: '1.5rem 1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Target */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            {[
              ['Target Handle', `@${report.handle}`],
              ['Platform', report.platform.toUpperCase()],
              ['Classification', report.classification],
              ['Risk Score', `${report.risk_score.toFixed(2)} / 100`],
              ['Current Status', STATUS_LABELS[report.status as CaseStatus] ?? report.status],
            ].map(([label, val]) => (
              <div key={label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.75rem 1rem' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>{label}</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{val}</div>
              </div>
            ))}
          </div>

          {/* Evidence Summary */}
          <div>
            <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: '1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BookOpen size={16} color="#b45309" /> Evidence Summary
            </h4>
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-default)',
              borderRadius: '6px', padding: '1rem',
              fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.65,
              whiteSpace: 'pre-line', fontFamily: 'var(--font-sans)',
            }}>
              {report.evidence_summary}
            </div>
          </div>

          {/* SHAP Reasons */}
          <div>
            <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: '1rem', marginBottom: '0.65rem' }}>
              SHAP Forensic Indicators
            </h4>
            <ul className="reasons-list">
              {report.reasons.map((r, i) => (
                <li key={i} className="reason-item">
                  <div className="reason-bullet">{i + 1}</div>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Basis */}
          <div>
            <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: '1rem', marginBottom: '0.65rem' }}>
              Legal Basis
            </h4>
            <div style={{
              background: 'rgba(99,102,241,0.06)',
              border: '1px solid rgba(99,102,241,0.25)',
              borderRadius: '6px',
              padding: '1rem 1.1rem',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)',
              lineHeight: 1.7,
            }}>
              {report.legal_basis}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// ── Case Detail Drawer ───────────────────────────────────────────────────────

function CaseDrawer({
  caseItem,
  onClose,
  onStatusUpdate,
  addToast,
}: {
  caseItem: Case;
  onClose: () => void;
  onStatusUpdate: (updated: Case) => void;
  addToast: (msg: string, type: Toast['type']) => void;
}) {
  const [updating, setUpdating] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [report, setReport] = useState<CaseReport | null>(null);
  const [reviewedBy, setReviewedBy] = useState(caseItem.reviewed_by ?? 'Unassigned');
  const nextStatus = NEXT_STATUS[caseItem.status];

  const handleAdvanceStatus = async () => {
    if (!nextStatus || updating) return;
    setUpdating(true);
    try {
      const updated = await updateCaseStatus(caseItem.id, nextStatus, reviewedBy || undefined);
      onStatusUpdate(updated);
      addToast(`Status advanced to ${STATUS_LABELS[nextStatus]}`, 'success');
    } catch (e: any) {
      addToast(e?.response?.data?.detail ?? 'Status update failed', 'error');
    } finally {
      setUpdating(false);
    }
  };

  const handleGenerateReport = async () => {
    if (generatingReport) return;
    setGeneratingReport(true);
    try {
      const r = await getCaseReport(caseItem.id);
      setReport(r);
      addToast('Report generated', 'success');
    } catch (e: any) {
      addToast(e?.response?.data?.detail ?? 'Report generation failed', 'error');
    } finally {
      setGeneratingReport(false);
    }
  };

  const c = STATUS_COLORS[caseItem.status];

  return (
    <>
      {/* Backdrop */}
      <div
        style={{ position: 'fixed', inset: 0, zIndex: 5000, background: 'rgba(28,25,23,0.4)' }}
        onClick={onClose}
      />

      {/* Drawer */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, zIndex: 5001,
        width: 'min(520px, 92vw)',
        background: 'var(--bg-panel)',
        borderLeft: '1px solid var(--border-default)',
        boxShadow: '-8px 0 40px rgba(28,25,23,0.12)',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        animation: 'slideInRight 0.22s ease',
      }}>

        {/* Drawer Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--border-default)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
          background: 'var(--bg-card)',
        }}>
          <div>
            <div className="eyebrow">Case Detail</div>
            <h3 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.15rem', marginTop: '0.15rem' }}>
              @{caseItem.handle}
            </h3>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: '3px', fontFamily: 'var(--font-mono)' }}>
              {caseItem.platform.toUpperCase()} · ID {caseItem.id.slice(0, 8)}…
            </div>
          </div>
          <button onClick={onClose} style={{ padding: '0.45rem', border: '1px solid var(--border-default)', background: 'var(--bg-panel)', borderRadius: '5px', color: 'var(--text-muted)' }}>
            <X size={16} />
          </button>
        </div>

        {/* Drawer Body */}
        <div style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', flex: 1 }}>

          {/* Quick Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem' }}>
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.75rem' }}>
              <div style={{ fontSize: '0.67rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>Risk Score</div>
              <div style={{ fontSize: '1.2rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: RISK_COLOR(caseItem.risk_score) }}>{caseItem.risk_score.toFixed(1)}</div>
            </div>
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.75rem' }}>
              <div style={{ fontSize: '0.67rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>Classification</div>
              <div style={{ fontSize: '0.88rem', fontWeight: 700, color: caseItem.classification === 'FAKE' ? '#dc2626' : '#d97706' }}>{caseItem.classification}</div>
            </div>
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.75rem' }}>
              <div style={{ fontSize: '0.67rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>Flagged</div>
              <div style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{formatDate(caseItem.created_at)}</div>
            </div>
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.75rem' }}>
              <div style={{ fontSize: '0.67rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>Reviewed By</div>
              <div style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{caseItem.reviewed_by ?? 'Unassigned'}</div>
            </div>
          </div>

          {/* Current Status */}
          <div>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Current Status</div>
            <StatusBadge status={caseItem.status} />
          </div>

          {/* SHAP Reasons */}
          <div>
            <h4 className="reasons-title" style={{ fontSize: '0.92rem' }}>
              <BookOpen size={15} color="#b45309" /> SHAP Decision Attribution
            </h4>
            <ul className="reasons-list">
              {caseItem.reasons.map((r, i) => (
                <li key={i} className="reason-item">
                  <div className="reason-bullet">{i + 1}</div>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Reviewed By Input */}
          {nextStatus && (
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
                Officer Name (for audit log)
              </div>
              <input
                type="text"
                className="form-input"
                style={{ width: '100%', margin: 0 }}
                placeholder="e.g. Inspector R. Sharma"
                value={reviewedBy}
                onChange={e => setReviewedBy(e.target.value)}
              />
            </div>
          )}

          {/* Advance Status Button */}
          {nextStatus && (
            <button
              onClick={handleAdvanceStatus}
              disabled={updating}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                padding: '0.75rem',
                background: STATUS_COLORS[nextStatus].color,
                color: '#fff',
                border: 'none',
                borderRadius: '5px',
                fontFamily: 'var(--font-serif)',
                fontWeight: 700,
                fontSize: '0.9rem',
                opacity: updating ? 0.6 : 1,
                cursor: updating ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
              }}>
              {updating ? <div className="spinner" /> : <ChevronRight size={16} />}
              Advance to: {STATUS_LABELS[nextStatus]}
            </button>
          )}

          {caseItem.status === 'TAKEDOWN_CONFIRMED' && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center',
              padding: '0.65rem',
              background: STATUS_COLORS.TAKEDOWN_CONFIRMED.bg,
              border: `1px solid ${STATUS_COLORS.TAKEDOWN_CONFIRMED.border}`,
              borderRadius: '5px',
              color: STATUS_COLORS.TAKEDOWN_CONFIRMED.color,
              fontWeight: 700, fontSize: '0.85rem',
            }}>
              <CheckCircle2 size={15} /> Takedown Confirmed — case closed
            </div>
          )}

          {/* Generate Report */}
          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
              padding: '0.7rem',
              background: 'var(--bg-card)',
              color: '#6366f1',
              border: '1px solid rgba(99,102,241,0.35)',
              borderRadius: '5px',
              fontFamily: 'var(--font-serif)',
              fontWeight: 700,
              fontSize: '0.88rem',
              opacity: generatingReport ? 0.6 : 1,
            }}>
            {generatingReport ? <div className="spinner" style={{ borderTopColor: '#6366f1', borderColor: 'rgba(99,102,241,0.3)' }} /> : <FileText size={15} />}
            {caseItem.report_generated ? 'Re-generate Report' : 'Generate Formal Report'}
          </button>

        </div>
      </div>

      {/* Report Modal (rendered on top of drawer) */}
      {report && <ReportModal report={report} onClose={() => setReport(null)} />}
    </>
  );
}

// ── Main EscalationView ──────────────────────────────────────────────────────

export function EscalationView({
  onEscalationTabActive,
}: {
  onEscalationTabActive?: () => void;
}) {
  const [cases, setCases] = useState<Case[]>([]);
  const [summary, setSummary] = useState<CaseSummary | null>(null);
  const [loadingCases, setLoadingCases] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [toastCounter, setToastCounter] = useState(0);
  const [statusFilter, setStatusFilter] = useState<CaseStatus | 'ALL'>('ALL');

  const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  }, []);

  const dismissToast = (id: number) => setToasts(prev => prev.filter(t => t.id !== id));

  const loadData = useCallback(async () => {
    setLoadingCases(true);
    setLoadingSummary(true);
    try {
      const [casesData, summaryData] = await Promise.all([getCases(), getCaseSummary()]);
      setCases(casesData);
      setSummary(summaryData);
    } catch (e) {
      addToast('Failed to load escalation data from backend', 'error');
    } finally {
      setLoadingCases(false);
      setLoadingSummary(false);
    }
  }, [addToast]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleStatusUpdate = (updated: Case) => {
    setCases(prev => prev.map(c => c.id === updated.id ? updated : c));
    setSelectedCase(updated);
    // Refresh summary counts
    getCaseSummary().then(setSummary).catch(() => {});
  };

  const filtered = statusFilter === 'ALL' ? cases : cases.filter(c => c.status === statusFilter);

  return (
    <div style={{ padding: '0' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.75rem' }}>
        <div className="eyebrow">ITBP / MHA — IT Rules 2021, Rule 3(1)(d)</div>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.65rem', color: 'var(--text-primary)', marginTop: '0.15rem' }}>
          Central Agency Escalation Centre
        </h2>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.35rem', maxWidth: '600px', lineHeight: 1.6 }}>
          Downstream escalation pipeline for flagged accounts. Tracks case status from detection through agency review, report generation, and platform takedown confirmation.
        </p>
      </div>

      {/* Summary Strip */}
      <SummaryStrip summary={summary} loading={loadingSummary} />

      {/* Cases Table */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-default)', borderRadius: '8px', boxShadow: '0 4px 12px rgba(28,25,23,0.05)' }}>
        {/* Table Toolbar */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Scale size={16} color="var(--accent-gold)" />
            <span style={{ fontSize: '0.9rem', fontFamily: 'var(--font-serif)', fontWeight: 700, color: 'var(--text-primary)' }}>
              Escalated Cases
            </span>
            <span style={{
              fontSize: '0.7rem', fontWeight: 700,
              background: 'rgba(180,83,9,0.12)', color: '#b45309',
              border: '1px solid rgba(180,83,9,0.25)',
              borderRadius: '12px', padding: '2px 8px',
            }}>{filtered.length}</span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            {/* Filter */}
            <select
              className="form-input custom-select"
              style={{ margin: 0, fontSize: '0.78rem', padding: '0.4rem 2rem 0.4rem 0.75rem', width: 'auto' }}
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value as CaseStatus | 'ALL')}
            >
              <option value="ALL">All Statuses</option>
              {STATUS_ORDER.map(s => (
                <option key={s} value={s}>{STATUS_LABELS[s]}</option>
              ))}
            </select>

            <button
              onClick={loadData}
              title="Refresh"
              style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.4rem 0.75rem',
                border: '1px solid var(--border-default)',
                background: 'var(--bg-card)', borderRadius: '5px',
                fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)',
              }}>
              <RefreshCw size={13} style={{ animation: loadingCases ? 'spin 0.8s linear infinite' : 'none' }} />
              Refresh
            </button>
          </div>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--bg-card)' }}>
                {['Handle', 'Platform', 'Risk Score', 'Classification', 'Status', 'Flagged', 'Actions'].map(h => (
                  <th key={h} style={{
                    padding: '0.7rem 1rem',
                    textAlign: 'left',
                    fontSize: '0.68rem',
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
              {loadingCases ? (
                <tr>
                  <td colSpan={7} style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                      <div className="spinner" style={{ borderTopColor: '#b45309', borderColor: 'rgba(180,83,9,0.2)' }} />
                      Loading cases…
                    </div>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                    No cases found{statusFilter !== 'ALL' ? ` with status "${STATUS_LABELS[statusFilter as CaseStatus]}"` : ''}.
                  </td>
                </tr>
              ) : (
                filtered.map((c, idx) => {
                  const nextS = NEXT_STATUS[c.status];
                  const nextC = nextS ? STATUS_COLORS[nextS] : null;
                  return (
                    <tr
                      key={c.id}
                      onClick={() => setSelectedCase(c)}
                      style={{
                        cursor: 'pointer',
                        background: idx % 2 === 0 ? 'var(--bg-panel)' : 'var(--bg-card)',
                        transition: 'background 0.15s',
                        borderBottom: '1px solid var(--border-subtle)',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                      onMouseLeave={e => (e.currentTarget.style.background = idx % 2 === 0 ? 'var(--bg-panel)' : 'var(--bg-card)')}
                    >
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                        @{c.handle}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{
                          fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase',
                          background: 'var(--bg-dark)', border: '1px solid var(--border-default)',
                          borderRadius: '3px', padding: '2px 7px', color: 'var(--text-secondary)',
                        }}>{c.platform === 'twitter' ? 'X / Twitter' : 'Meta'}</span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.88rem', color: RISK_COLOR(c.risk_score) }}>
                        {c.risk_score.toFixed(1)}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: c.classification === 'FAKE' ? '#dc2626' : '#d97706' }}>
                          {c.classification}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <StatusBadge status={c.status} />
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontSize: '0.77rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                        {formatDate(c.created_at)}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                          <button
                            onClick={() => setSelectedCase(c)}
                            style={{
                              display: 'flex', alignItems: 'center', gap: '3px',
                              padding: '4px 9px', borderRadius: '4px',
                              border: '1px solid var(--border-default)',
                              background: 'var(--bg-card)',
                              fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-secondary)',
                            }}>
                            <ChevronRight size={12} /> View
                          </button>
                          {nextS && nextC && (
                            <button
                              onClick={async (e) => {
                                e.stopPropagation();
                                try {
                                  const updated = await updateCaseStatus(c.id, nextS);
                                  setCases(prev => prev.map(x => x.id === updated.id ? updated : x));
                                  getSummaryQuietly(setSummary);
                                  addToast(`Case advanced to ${STATUS_LABELS[nextS]}`, 'success');
                                } catch (err: any) {
                                  addToast(err?.response?.data?.detail ?? 'Update failed', 'error');
                                }
                              }}
                              style={{
                                display: 'flex', alignItems: 'center', gap: '3px',
                                padding: '4px 9px', borderRadius: '4px',
                                border: `1px solid ${nextC.border}`,
                                background: nextC.bg,
                                fontSize: '0.72rem', fontWeight: 600, color: nextC.color,
                              }}>
                              → {STATUS_LABELS[nextS].split(' ')[0]}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Drawer */}
      {selectedCase && (
        <CaseDrawer
          caseItem={selectedCase}
          onClose={() => setSelectedCase(null)}
          onStatusUpdate={handleStatusUpdate}
          addToast={addToast}
        />
      )}

      {/* Toasts */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Keyframe styles */}
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(40px); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
        @keyframes fadeInUp {
          from { transform: translateY(8px); opacity: 0; }
          to   { transform: translateY(0);   opacity: 1; }
        }
      `}</style>
    </div>
  );
}

// Helper used inline in the table row quick-advance button
async function getSummaryQuietly(setSummary: (s: CaseSummary) => void) {
  try {
    const s = await getCaseSummary();
    setSummary(s);
  } catch {}
}
