import React, { useState, useEffect, useCallback } from 'react';
import { SessionStatus, PlatformSessionInfo } from './types';
import { getSessionStatus, captureSession, revokeSession } from './api';
import { CheckCircle2, AlertTriangle, XCircle, Link, Unlink, RefreshCw, Shield } from 'lucide-react';

type Platform = 'twitter' | 'instagram' | 'facebook';

const PLATFORM_META: Record<Platform, {
  label: string;
  icon: string;
  color: string;
  loginNote: string;
  reliabilityBefore: string;
  reliabilityAfter: string;
}> = {
  twitter: {
    label: 'X',
    icon: '𝕏',
    color: '#1a1a2e',
    loginNote: 'A Chromium window will open X.com. Log in normally (2FA is fine). The window closes automatically once login is detected.',
    reliabilityBefore: '~20%',
    reliabilityAfter: '~85%',
  },
  instagram: {
    label: 'Instagram',
    icon: '📸',
    color: '#833ab4',
    loginNote: 'A Chromium window will open Instagram. Log in with your account (any personal account works). Your password is never stored — only the session cookie.',
    reliabilityBefore: '~15%',
    reliabilityAfter: '~80%',
  },
  facebook: {
    label: 'Facebook',
    icon: '👥',
    color: '#1877f2',
    loginNote: 'Most public Facebook pages work without login. Click Connect only if you need to scan private profiles.',
    reliabilityBefore: '~30%',
    reliabilityAfter: '~90%',
  },
};

function formatDate(iso: string | null): string {
  if (!iso) return 'Never';
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

interface PlatformCardProps {
  platform: Platform;
  info: PlatformSessionInfo;
  onConnect: (platform: Platform) => void;
  onRevoke: (platform: Platform) => void;
  isCapturing: boolean;
}

function PlatformCard({ platform, info, onConnect, onRevoke, isCapturing }: PlatformCardProps) {
  const meta = PLATFORM_META[platform];
  const isConnected = info.connected;
  const isBusy = isCapturing;

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: `1px solid ${isConnected ? 'rgba(34,197,94,0.35)' : 'var(--border-default)'}`,
      borderRadius: '10px',
      padding: '1.2rem 1.4rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
      transition: 'border-color 0.2s',
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '1.4rem', lineHeight: 1 }}>{meta.icon}</span>
          <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            {meta.label}
          </span>
        </div>

        {/* Status badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem',
          padding: '3px 10px',
          borderRadius: '20px',
          fontSize: '0.72rem',
          fontWeight: 700,
          letterSpacing: '0.04em',
          background: isConnected ? 'rgba(34,197,94,0.12)' : 'rgba(156,163,175,0.1)',
          color: isConnected ? '#22c55e' : 'var(--text-muted)',
          border: `1px solid ${isConnected ? 'rgba(34,197,94,0.3)' : 'var(--border-default)'}`,
        }}>
          {isConnected
            ? <><CheckCircle2 size={11} /> CONNECTED</>
            : <><XCircle size={11} /> NOT CONNECTED</>
          }
        </div>
      </div>

      {/* Session meta */}
      {isConnected && (
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
          <span>🕐 Connected: {formatDate(info.captured_at)}</span>
          <span>🍪 Cookies: {info.cookies_count}</span>
        </div>
      )}

      {/* Reliability row */}
      <div style={{
        background: 'var(--bg-input)',
        borderRadius: '6px',
        padding: '0.5rem 0.75rem',
        fontSize: '0.76rem',
        color: 'var(--text-secondary)',
        display: 'flex',
        gap: '1.5rem',
      }}>
        <span>Before: <b style={{ color: '#f87171' }}>{meta.reliabilityBefore}</b></span>
        <span>After connecting: <b style={{ color: '#4ade80' }}>{meta.reliabilityAfter}</b></span>
      </div>

      {/* Login hint */}
      {!isConnected && (
        <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.5 }}>
          {meta.loginNote}
        </p>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.2rem' }}>
        <button
          onClick={() => onConnect(platform)}
          disabled={isBusy}
          style={{
            flex: 1,
            padding: '0.5rem 1rem',
            borderRadius: '6px',
            border: 'none',
            background: isConnected
              ? 'rgba(59,130,246,0.15)'
              : 'linear-gradient(135deg, #3b82f6, #6366f1)',
            color: isConnected ? '#60a5fa' : 'white',
            fontWeight: 600,
            fontSize: '0.8rem',
            cursor: isBusy ? 'not-allowed' : 'pointer',
            opacity: isBusy ? 0.6 : 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.4rem',
            transition: 'opacity 0.2s',
          }}
        >
          {isBusy
            ? <><RefreshCw size={13} className="spin" /> Opening browser...</>
            : isConnected
              ? <><RefreshCw size={13} /> Reconnect</>
              : <><Link size={13} /> Connect {meta.label}</>
          }
        </button>

        {isConnected && (
          <button
            onClick={() => onRevoke(platform)}
            disabled={isBusy}
            style={{
              padding: '0.5rem 0.8rem',
              borderRadius: '6px',
              border: '1px solid rgba(239,68,68,0.3)',
              background: 'rgba(239,68,68,0.08)',
              color: '#f87171',
              fontWeight: 600,
              fontSize: '0.8rem',
              cursor: isBusy ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <Unlink size={13} /> Disconnect
          </button>
        )}
      </div>
    </div>
  );
}

interface SessionManagerProps {
  onSessionChange?: () => void;
}

const emptyStatus: SessionStatus = {
  twitter: { connected: false, captured_at: null, cookies_count: 0 },
  instagram: { connected: false, captured_at: null, cookies_count: 0 },
  facebook: { connected: false, captured_at: null, cookies_count: 0 },
};

export function SessionManager({ onSessionChange }: SessionManagerProps) {
  const [status, setStatus] = useState<SessionStatus>(emptyStatus);
  const [capturingPlatform, setCapturingPlatform] = useState<Platform | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const s = await getSessionStatus();
      if (s) setStatus(s);
    } catch {
      // Backend may be offline or unreachable on remote hosting
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const handleConnect = async (platform: Platform) => {
    setCapturingPlatform(platform);
    setMessage({ type: 'info', text: `Opening Chromium window for ${PLATFORM_META[platform].label}... Log in normally. This window will close automatically.` });
    try {
      const res = await captureSession(platform);
      setMessage({ type: 'success', text: res.message });
      await loadStatus();
      onSessionChange?.();
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      setMessage({ type: 'error', text: `Failed to capture session: ${detail}` });
    } finally {
      setCapturingPlatform(null);
    }
  };

  const handleRevoke = async (platform: Platform) => {
    try {
      const res = await revokeSession(platform);
      setMessage({ type: 'info', text: res.message });
      await loadStatus();
      onSessionChange?.();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Failed to disconnect session.' });
    }
  };

  const displayStatus = status;

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
          <Shield size={20} color="#6366f1" />
          <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Platform Session Manager
          </h2>
        </div>
        <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          Connect your social accounts once to dramatically improve scan accuracy.
          Sessions are stored locally as browser cookies — <b>your password is never saved</b>.
          Reconnect every ~30 days when sessions expire.
        </p>
      </div>

      {/* Toast message */}
      {message && (
        <div style={{
          marginBottom: '1rem',
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          fontSize: '0.82rem',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.5rem',
          background: message.type === 'success'
            ? 'rgba(34,197,94,0.1)'
            : message.type === 'error'
              ? 'rgba(239,68,68,0.1)'
              : 'rgba(99,102,241,0.1)',
          border: `1px solid ${message.type === 'success'
            ? 'rgba(34,197,94,0.3)'
            : message.type === 'error'
              ? 'rgba(239,68,68,0.3)'
              : 'rgba(99,102,241,0.3)'}`,
          color: message.type === 'success'
            ? '#4ade80'
            : message.type === 'error'
              ? '#f87171'
              : '#a5b4fc',
        }}>
          {message.type === 'success' && <CheckCircle2 size={15} style={{ flexShrink: 0, marginTop: '1px' }} />}
          {message.type === 'error' && <XCircle size={15} style={{ flexShrink: 0, marginTop: '1px' }} />}
          {message.type === 'info' && <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: '1px' }} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Platform cards */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Loading session status...
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {(['twitter', 'instagram', 'facebook'] as Platform[]).map((platform) => (
            <PlatformCard
              key={platform}
              platform={platform}
              info={displayStatus[platform]}
              onConnect={handleConnect}
              onRevoke={handleRevoke}
              isCapturing={capturingPlatform === platform}
            />
          ))}
        </div>
      )}

      {/* Privacy note */}
      <div style={{
        marginTop: '1.5rem',
        padding: '0.75rem 1rem',
        borderRadius: '8px',
        background: 'var(--bg-input)',
        border: '1px solid var(--border-default)',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
        lineHeight: 1.6,
      }}>
        🔐 <b>Privacy</b>: Sessions are stored in <code>backend/sessions/</code> as JSON files
        on your local machine only. They are never uploaded to any server.
        You can revoke any session at any time using the Disconnect button above.
      </div>
    </div>
  );
}
