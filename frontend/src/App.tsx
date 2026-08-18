import React, { useState, useEffect } from 'react';
import { PRESET_ACCOUNTS } from './presets';
import { analyzeAccount, checkHealth } from './api';
import { AccountFeatures, AnalyzeResponse } from './types';
import { BatchView } from './BatchView';
import { CheckCircle2, AlertTriangle, XCircle, Search, BookOpen, RotateCcw } from 'lucide-react';
import './index.css';

export default function App() {
  const [platform, setPlatform] = useState<'twitter' | 'meta'>('twitter');
  const [selectedPresetId, setSelectedPresetId] = useState<string>('tw_bot');
  const [formData, setFormData] = useState<AccountFeatures>(PRESET_ACCOUNTS[0].features);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [error, setError] = useState<string | null>(null);

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
  };

  return (
    <div className="container">
      {/* PUBLICATION EDITORIAL HEADER */}
      <header className="app-header">
        <div>
          <div className="eyebrow">SIH1775 • SPECIAL INTELLIGENCE REPORT</div>
          <h1 className="publication-title">The Bot & Threat Detector</h1>
          <div className="publication-issue">Dual-Platform XGBoost Model Inference & SHAP Attribution</div>
        </div>

        <div className="status-badge" style={{ borderColor: backendStatus === 'online' ? 'rgba(22, 163, 74, 0.4)' : 'rgba(220, 38, 38, 0.4)', color: backendStatus === 'online' ? '#16a34a' : '#dc2626', background: backendStatus === 'online' ? 'rgba(22, 163, 74, 0.08)' : 'rgba(220, 38, 38, 0.08)' }}>
          <div className="status-dot" style={{ background: backendStatus === 'online' ? '#16a34a' : '#dc2626' }} />
          <span>API: {backendStatus.toUpperCase()}</span>
        </div>
      </header>

      {/* MAIN DASHBOARD GRID */}
      <div className="dashboard-grid">
        {/* LEFT COLUMN: EDITORIAL FORM & PRESETS */}
        <div className="editorial-panel" style={{ padding: '1.75rem' }}>
          {/* SECTION 01: PLATFORM SELECTION */}
          <div className="section-header">
            <h2 className="section-title">
              <span className="section-num">01 /</span> Target Platform Context
            </h2>
          </div>

          <div className="platform-tabs" style={{ marginBottom: '1.75rem' }}>
            <button
              className={`tab-btn ${platform === 'twitter' ? 'active' : ''}`}
              onClick={() => handlePlatformSwitch('twitter')}
            >
              🐦 Twitter / X
            </button>
            <button
              className={`tab-btn ${platform === 'meta' ? 'active' : ''}`}
              onClick={() => handlePlatformSwitch('meta')}
            >
              📸 Meta (Instagram & Facebook)
            </button>
          </div>

          {/* SECTION 02: PRESETS */}
          <div className="section-header">
            <h3 className="section-title">
              <span className="section-num">02 /</span> Sample Telemetry Profiles
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
              <span className="section-num">03 /</span> Account Telemetry Metrics
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
                  <div className="spinner" /> Analyzing Account Metrics...
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
                      <div className="reason-bullet">§{idx + 1}</div>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">📰</div>
              <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '1.25rem' }}>Report Standby</h3>
              <p style={{ maxWidth: '340px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Select a sample telemetry profile on the left or enter custom account metrics, then click <b>Analyze Account Security Risk</b> to generate a report.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* SECTION 04: BATCH CSV ANALYSIS */}
      <BatchView />
    </div>
  );
}
