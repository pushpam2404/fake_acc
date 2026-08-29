import React, { useState, useEffect } from 'react';
import { PRESET_ACCOUNTS } from './presets';
import { analyzeAccount, checkHealth, analyzeUrl, downloadReport } from './api';
import { AccountFeatures, AnalyzeResponse } from './types';
import { SessionManager } from './SessionManager';
import { CheckCircle2, AlertTriangle, XCircle, Search, BookOpen, RotateCcw, FileDown, Sparkles, Shield, LayoutDashboard, KeyRound } from 'lucide-react';
import { NetworkGraph } from './NetworkGraph';
import { MediaAuditView } from './MediaAuditView';
import './index.css';

export default function App() {
  const [activeTab, setActiveTab] = useState<'scan' | 'sessions'>('scan');
  const [platform, setPlatform] = useState<'twitter' | 'meta'>('twitter');
  const [selectedPresetId, setSelectedPresetId] = useState<string>('tw_bot');
  const [formData, setFormData] = useState<AccountFeatures>(PRESET_ACCOUNTS[0].features);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [error, setError] = useState<string | null>(null);
  const [profileUrl, setProfileUrl] = useState<string>('');
  const [scraping, setScraping] = useState<boolean>(false);

  // Check backend health on mount
  useEffect(() => {
    checkHealth()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const currentPresets = PRESET_ACCOUNTS.filter((p) => p.platform === platform);

  const handlePlatformSwitch = (newPlatform: 'twitter' | 'meta') => {
    setPlatform(newPlatform);
    const firstPreset = PRESET_ACCOUNTS.find((p) => p.platform === newPlatform);
    if (firstPreset) {
      setSelectedPresetId(firstPreset.id);
      setFormData({ ...firstPreset.features });
    }
    setResult(null);
    setError(null);
  };

  const handleSelectPreset = (presetId: string) => {
    setSelectedPresetId(presetId);
    const preset = PRESET_ACCOUNTS.find((p) => p.id === presetId);
    if (preset) {
      setFormData({ ...preset.features });
    }
    setResult(null);
    setError(null);
  };

  const handleInputChange = (field: keyof AccountFeatures, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: typeof value === 'number' && isNaN(value) ? 0 : value,
    }));
  };

  const handleAnalyze = async () => {
    if (loading) return; // Prevent double click mid-request
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload: AccountFeatures = {
        ...formData,
        platform,
      };
      const res = await analyzeAccount(payload);
      setResult(res);
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          'Failed to connect to backend API server at http://localhost:8000/analyze'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setProfileUrl('');
  };

  const handleAnalyzeUrl = async () => {
    if (!profileUrl.trim()) return;
    setScraping(true);
    setError(null);
    setResult(null);

    try {
      const res = await analyzeUrl(profileUrl);
      setResult(res);
      if (res.raw_features) {
        setFormData(res.raw_features);
        if (res.platform === 'twitter' || res.platform === 'meta') {
          setPlatform(res.platform as 'twitter' | 'meta');
        }
      }
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          'Failed to scan profile URL. The server may be offline or rate-limited.'
      );
    } finally {
      setScraping(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!result) return;
    try {
      const username = result.username || formData.username || 'target_profile';
      const blob = await downloadReport(username, formData, result);
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `ITBP_Forensic_Report_${username}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error(err);
      setError('Failed to export forensic report PDF.');
    }
  };


  return (
    <div className="container">
      {/* PUBLICATION EDITORIAL HEADER */}
      <header className="app-header">
        <div>
          <div className="eyebrow">CYBER THREAT INTELLIGENCE</div>
          <h1 className="publication-title">The Bot & Threat Detector</h1>
          <div className="publication-issue">Automated Multi-Platform Profile Forensic & Inauthentic Behavior Analysis</div>
        </div>
      </header>

      {/* TOP NAVIGATION TABS */}
      <div style={{
        display: 'flex',
        gap: '0.75rem',
        marginBottom: '1.75rem',
        borderBottom: '1px solid var(--border-default)',
        paddingBottom: '0.75rem',
      }}>
        <button
          onClick={() => setActiveTab('scan')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.1rem',
            borderRadius: '6px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            border: activeTab === 'scan' ? '1px solid #6366f1' : '1px solid var(--border-default)',
            background: activeTab === 'scan' ? 'rgba(99,102,241,0.15)' : 'var(--bg-card)',
            color: activeTab === 'scan' ? '#a5b4fc' : 'var(--text-secondary)',
            transition: 'all 0.2s',
          }}
        >
          <LayoutDashboard size={16} /> Real-Time URL & Telemetry Scan
        </button>

        <button
          onClick={() => setActiveTab('sessions')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.1rem',
            borderRadius: '6px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            border: activeTab === 'sessions' ? '1px solid #6366f1' : '1px solid var(--border-default)',
            background: activeTab === 'sessions' ? 'rgba(99,102,241,0.15)' : 'var(--bg-card)',
            color: activeTab === 'sessions' ? '#a5b4fc' : 'var(--text-secondary)',
            transition: 'all 0.2s',
          }}
        >
          <KeyRound size={16} /> Platform Sessions & Auth
        </button>
      </div>

      {activeTab === 'scan' && (
        <div className="dashboard-grid">
        {/* LEFT COLUMN: EDITORIAL FORM & PRESETS */}
        <div className="editorial-panel" style={{ padding: '1.75rem' }}>
          {/* SECTION 00: PROFILE URL SCAN */}
          <div className="section-header">
            <h2 className="section-title">
              <span className="section-num">01 /</span> Scan Active Profile Link
            </h2>
          </div>

          <div style={{ marginBottom: '1.75rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                placeholder="e.g. https://x.com/username or https://instagram.com/username"
                className="form-input"
                style={{ flex: 1, margin: 0 }}
                value={profileUrl}
                onChange={(e) => setProfileUrl(e.target.value)}
              />
              <button
                className="analyze-btn"
                style={{ width: 'auto', marginTop: 0, padding: '0 1.25rem', whiteSpace: 'nowrap' }}
                onClick={handleAnalyzeUrl}
                disabled={scraping || !profileUrl}
              >
                {scraping ? (
                  <>
                    <div className="spinner" /> Analyzing...
                  </>
                ) : (
                  'Deep Scan URL'
                )}
              </button>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '6px', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              <span>Supports public Instagram, X, and Facebook profile URLs</span>
            </div>
          </div>

          {/* SECTION 01: PLATFORM SELECTION */}
          <div className="section-header">
            <h2 className="section-title">
              <span className="section-num">02 /</span> Target Platform Context
            </h2>
          </div>

          <div className="platform-tabs" style={{ marginBottom: '1.75rem' }}>
            <button
              className={`tab-btn ${platform === 'twitter' ? 'active' : ''}`}
              onClick={() => handlePlatformSwitch('twitter')}
            >
              X
            </button>
            <button
              className={`tab-btn ${platform === 'meta' ? 'active' : ''}`}
              onClick={() => handlePlatformSwitch('meta')}
            >
              Meta (Instagram & Facebook)
            </button>
          </div>

          {/* SECTION 02: PRESETS */}
          <div className="section-header">
            <h3 className="section-title">
              <span className="section-num">03 /</span> Sample Telemetry Profiles
            </h3>
          </div>

          <div className="presets-grid">
            {currentPresets.map((preset) => (
              <div
                key={preset.id}
                className={`preset-card ${selectedPresetId === preset.id ? 'active' : ''}`}
                onClick={() => handleSelectPreset(preset.id)}
                title={preset.description}
              >
                <div className="preset-name">{preset.name}</div>
                <div className="preset-desc">{preset.description}</div>
              </div>
            ))}
          </div>

          {/* SECTION 03: FORM METRICS */}
          <div className="section-header">
            <h3 className="section-title">
              <span className="section-num">04 /</span> Account Telemetry Metrics
            </h3>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Followers Count</label>
              <input
                type="number"
                className="form-input"
                value={formData.followers}
                onChange={(e) => handleInputChange('followers', parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Following Count</label>
              <input
                type="number"
                className="form-input"
                value={formData.following}
                onChange={(e) => handleInputChange('following', parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Total Posts Count</label>
              <input
                type="number"
                className="form-input"
                value={formData.post_count}
                onChange={(e) => handleInputChange('post_count', parseInt(e.target.value) || 0)}
              />
            </div>

            {platform === 'twitter' ? (
              <>
                <div className="form-group">
                  <label className="form-label">Account Age (Days)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={formData.account_age_days || 0}
                    onChange={(e) => handleInputChange('account_age_days', parseInt(e.target.value) || 0)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Verified Badge (0/1)</label>
                  <select
                    className="form-input custom-select"
                    value={formData.verified || 0}
                    onChange={(e) => handleInputChange('verified', parseInt(e.target.value))}
                  >
                    <option value={0}>0 (Unverified)</option>
                    <option value={1}>1 (Verified Blue Check)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Username Handle</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.username || ''}
                    onChange={(e) => handleInputChange('username', e.target.value)}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">Profile Picture (0/1)</label>
                  <select
                    className="form-input custom-select"
                    value={formData.has_profile_pic || 0}
                    onChange={(e) => handleInputChange('has_profile_pic', parseInt(e.target.value))}
                  >
                    <option value={0}>0 (Default Avatar)</option>
                    <option value={1}>1 (Valid Avatar)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Bio Description Length</label>
                  <input
                    type="number"
                    className="form-input"
                    value={formData.bio_length || 0}
                    onChange={(e) => handleInputChange('bio_length', parseInt(e.target.value) || 0)}
                  />
                </div>
              </>
            )}
          </div>

          <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
            <button className="analyze-btn" onClick={handleAnalyze} disabled={loading} style={{ flex: 1, marginTop: 0 }}>
              {loading ? (
                <>
                  <div className="spinner" /> Analyzing...
                </>
              ) : (
                <>
                  <Search size={18} /> Analyze Account Security Risk
                </>
              )}
            </button>

            <button
              className="analyze-btn"
              onClick={handleReset}
              style={{ width: "auto", marginTop: 0, background: "var(--bg-card)", border: "1px solid var(--border-default)", color: "var(--text-secondary)" }}
              title="Reset Results"
            >
              <RotateCcw size={16} /> Reset
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: EDITORIAL REPORT PANEL */}
        <div className="editorial-panel result-card">
          {error && (
            <div className="alert-error">
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}

          {result ? (
            <div>
              {/* CLASSIFICATION BADGE */}
              <div className="classification-header">
                <div>
                  <div className="eyebrow" style={{ fontSize: '0.65rem' }}>
                    CONTEXT: {result.platform.toUpperCase()}
                  </div>
                  <h2 style={{ fontSize: '1.6rem', marginTop: '0.15rem' }}>Analysis Finding</h2>
                </div>

                <div className={`risk-badge ${result.classification}`}>
                  {result.classification === 'FAKE' && <XCircle size={18} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />}
                  {result.classification === 'SUSPICIOUS' && <AlertTriangle size={18} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />}
                  {result.classification === 'REAL' && <CheckCircle2 size={18} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />}
                  {result.classification}
                </div>
              </div>

              {/* IDENTITY INFO */}
              {result.username && (
                <div style={{
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-default)',
                  borderRadius: '6px',
                  padding: '0.75rem 1rem',
                  marginTop: '0.75rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                  fontSize: '0.85rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--text-muted)', minWidth: '110px' }}>Handle:</span>
                    <span className="mono" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>@{result.username}</span>
                  </div>
                  {result.display_name && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ color: 'var(--text-muted)', minWidth: '110px' }}>Display Name:</span>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{result.display_name}</span>
                    </div>
                  )}
                </div>
              )}

              {/* RISK SCORE METER */}
              <div className="meter-container">
                <div className="meter-header">
                  <span>Assessed Risk Score</span>
                  <span className="mono" style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontWeight: 700 }}>
                    {result.risk_score.toFixed(2)} / 100
                  </span>
                </div>
                <div className="meter-bar-bg">
                  <div
                    className={`meter-bar-fill ${result.classification}`}
                    style={{ width: `${Math.min(100, Math.max(0, result.risk_score))}%` }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                  <span>0% (Authentic)</span>
                  <span>Confidence: {(result.confidence * 100).toFixed(2)}%</span>
                  <span>100% (Fake/Bot)</span>
                </div>
              </div>

              {/* SHAP EXPLANATION REASONS */}
              <div>
                <h3 className="reasons-title">
                  <BookOpen size={18} color="#b45309" /> SHAP Decision Attribution
                </h3>
                <ul className="reasons-list">
                  {result.reasons.map((reason, idx) => (
                    <li key={idx} className="reason-item">
                      <div className="reason-bullet">{idx + 1}</div>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* MULTIMODAL MEDIA & PHISHING AUDIT */}
              <MediaAuditView
                contentAnalysis={result.content_analysis}
                posts={result.posts}
                avatarUrl={result.avatar_url}
                bio={result.bio}
                externalUrl={result.external_url}
                username={result.username}
              />

              {/* CO-OCCURRENCE NETWORK GRAPH */}
              {result.network_graph && (
                <NetworkGraph data={result.network_graph} />
              )}

              {/* PDF EXPORT BUTTON */}

              <button
                className="analyze-btn"
                onClick={handleDownloadReport}
                style={{
                  marginTop: '1.75rem',
                  width: '100%',
                  background: '#b91c1c',
                  color: 'white',
                  display: 'flex',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  alignItems: 'center',
                  fontWeight: 600,
                  border: 'none',
                  borderRadius: '4px',
                  padding: '0.75rem'
                }}
              >
                <FileDown size={18} /> Export Forensic Case File (PDF)
              </button>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon" style={{ marginBottom: '0.6rem' }}>
                <Shield size={36} color="#6366f1" />
              </div>
              <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '1.25rem', fontFamily: 'var(--font-serif)' }}>
                Forensic Investigation Standby
              </h3>
              <p style={{ maxWidth: '360px', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                Paste any public <b>Instagram</b>, <b>X</b>, or <b>Facebook</b> profile link above and click <b>Deep Scan URL</b>, or select sample telemetry on the left to run an assessment.
              </p>
            </div>
          )}
        </div>
      </div>
    )}

      {activeTab === 'sessions' && (
        <div className="editorial-panel" style={{ padding: '2rem' }}>
          <SessionManager />
        </div>
      )}
    </div>
  );
}
