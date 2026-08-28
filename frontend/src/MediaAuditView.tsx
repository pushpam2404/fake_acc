import React from 'react';
import { ShieldAlert, AlertTriangle, Link as LinkIcon, Sparkles, Layers, Image as ImageIcon, CheckCircle, ExternalLink } from 'lucide-react';
import { ContentAnalysis, PostMediaItem } from './types';

interface MediaAuditViewProps {
  contentAnalysis?: ContentAnalysis;
  posts?: PostMediaItem[];
  avatarUrl?: string;
  bio?: string;
  externalUrl?: string;
  username?: string;
}

export function MediaAuditView({
  contentAnalysis,
  posts,
  avatarUrl,
  bio,
  externalUrl,
  username,
}: MediaAuditViewProps) {
  if (!contentAnalysis && (!posts || posts.length === 0)) {
    return null;
  }

  const threatLevel = contentAnalysis?.phishing_threat_level || 'LOW';
  const threatBadgeColor =
    threatLevel === 'CRITICAL'
      ? '#dc2626'
      : threatLevel === 'ELEVATED'
      ? '#ea580c'
      : threatLevel === 'MODERATE'
      ? '#d97706'
      : '#16a34a';

  const simScore = contentAnalysis?.caption_similarity?.similarity_score || 0;
  const isRepetitive = contentAnalysis?.caption_similarity?.is_repetitive || false;

  return (
    <div
      style={{
        marginTop: '1.5rem',
        padding: '1.25rem',
        border: '1px solid var(--border-default)',
        borderRadius: '8px',
        background: 'var(--bg-card)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
      }}
    >
      {/* SECTION HEADER */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-default)',
          paddingBottom: '0.75rem',
          marginBottom: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles size={18} color="#9333ea" />
          <h4
            style={{
              margin: 0,
              fontSize: '0.9rem',
              color: 'var(--text-primary)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontWeight: 700,
            }}
          >
            Playwright Multimodal & Media Forensic Audit
          </h4>
        </div>

        {contentAnalysis && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '3px 8px',
              borderRadius: '4px',
              background: `${threatBadgeColor}15`,
              border: `1px solid ${threatBadgeColor}40`,
              color: threatBadgeColor,
              fontSize: '0.75rem',
              fontWeight: 700,
            }}
          >
            <ShieldAlert size={14} />
            <span>THREAT: {threatLevel}</span>
          </div>
        )}
      </div>

      {/* PROFILE EXTRACTED HEADER (AVATAR + BIO + OUTBOUND LINK) */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          alignItems: 'flex-start',
          background: 'rgba(15, 23, 42, 0.02)',
          border: '1px solid var(--border-default)',
          borderRadius: '6px',
          padding: '0.85rem',
          marginBottom: '1rem',
        }}
      >
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt={username || 'Avatar'}
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              objectFit: 'cover',
              border: '2px solid var(--border-default)',
              flexShrink: 0,
            }}
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        ) : (
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: '#e2e8f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <ImageIcon size={24} color="#64748b" />
          </div>
        )}

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '4px' }}>
            <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
              @{username || 'target_profile'}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', background: 'rgba(15, 23, 42, 0.06)', padding: '1px 6px', borderRadius: '3px' }}>
              Headless Chromium Verified
            </span>
          </div>

          <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>
            {bio || <i style={{ color: 'var(--text-secondary)' }}>No biography description present on profile.</i>}
          </p>

          {externalUrl && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '6px', fontSize: '0.75rem' }}>
              <LinkIcon size={12} color="#64748b" />
              <span style={{ color: 'var(--text-secondary)' }}>Outbound:</span>
              <a
                href={externalUrl}
                target="_blank"
                rel="noreferrer"
                style={{
                  color: contentAnalysis?.outbound_link_audit?.risk_level === 'HIGH' ? '#dc2626' : '#2563eb',
                  textDecoration: 'underline',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '2px',
                }}
              >
                {externalUrl} <ExternalLink size={10} />
              </a>
              {contentAnalysis?.outbound_link_audit?.risk_level === 'HIGH' && (
                <span style={{ background: '#fee2e2', color: '#b91c1c', fontSize: '0.65rem', padding: '1px 5px', borderRadius: '3px', fontWeight: 600 }}>
                  ⚠️ High-Risk Shortener
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* NLP & NEURAL SEMANTICS GAUGES */}
      {contentAnalysis && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
          {/* Caption Similarity Meter */}
          <div
            style={{
              border: '1px solid var(--border-default)',
              borderRadius: '6px',
              padding: '0.75rem',
              background: 'rgba(15, 23, 42, 0.02)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Neural Caption Uniformity
              </span>
              <span
                className="mono"
                style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  color: isRepetitive ? '#dc2626' : '#16a34a',
                }}
              >
                {simScore}%
              </span>
            </div>

            <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${Math.min(100, simScore)}%`,
                  height: '100%',
                  background: isRepetitive ? 'linear-gradient(90deg, #f59e0b, #dc2626)' : '#16a34a',
                  transition: 'width 0.5s ease',
                }}
              />
            </div>

            <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '5px' }}>
              {contentAnalysis.caption_similarity?.verdict || 'Analysis completed.'}
            </div>
          </div>

          {/* Phishing / Threat Weight Meter */}
          <div
            style={{
              border: '1px solid var(--border-default)',
              borderRadius: '6px',
              padding: '0.75rem',
              background: 'rgba(15, 23, 42, 0.02)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Content Fraud & Threat Score
              </span>
              <span
                className="mono"
                style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  color: threatBadgeColor,
                }}
              >
                {contentAnalysis.content_risk_score} / 100
              </span>
            </div>

            <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${Math.min(100, contentAnalysis.content_risk_score)}%`,
                  height: '100%',
                  background: threatBadgeColor,
                  transition: 'width 0.5s ease',
                }}
              />
            </div>

            <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '5px' }}>
              Engine: <span className="mono" style={{ fontWeight: 600 }}>{contentAnalysis.caption_similarity?.method || 'Neural NLP'}</span>
            </div>
          </div>
        </div>
      )}

      {/* PHISHING & FRAUD FINDINGS LIST */}
      {contentAnalysis && contentAnalysis.phishing_indicators.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#dc2626', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={14} /> Active Phishing & Semantic Anomaly Triggers ({contentAnalysis.phishing_indicators.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {contentAnalysis.phishing_indicators.map((ind, i) => (
              <div
                key={i}
                style={{
                  fontSize: '0.72rem',
                  color: '#991b1b',
                  background: '#fef2f2',
                  border: '1px solid #fecaca',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  lineHeight: 1.3,
                }}
              >
                • {ind}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RECENT POSTS SCRAPED MEDIA GALLERY */}
      {posts && posts.length > 0 && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Layers size={14} /> Extracted Post Media Gallery ({posts.length} Posts)
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
              Headless DOM Crawl
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {posts.map((post, idx) => (
              <div
                key={post.id || idx}
                style={{
                  border: '1px solid var(--border-default)',
                  borderRadius: '6px',
                  overflow: 'hidden',
                  background: 'var(--bg-card)',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <div style={{ position: 'relative', width: '100%', height: '110px', background: '#0f172a' }}>
                  <img
                    src={post.thumbnail_url}
                    alt={`Post ${idx + 1}`}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                    }}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src =
                        'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=80';
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '4px',
                      left: '4px',
                      background: 'rgba(15, 23, 42, 0.8)',
                      color: '#f8fafc',
                      fontSize: '0.65rem',
                      padding: '1px 5px',
                      borderRadius: '3px',
                      fontFamily: 'monospace',
                    }}
                  >
                    #{idx + 1} • {post.timestamp || 'Recent'}
                  </div>
                </div>

                <div style={{ padding: '6px 8px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <p
                    style={{
                      margin: 0,
                      fontSize: '0.7rem',
                      color: 'var(--text-primary)',
                      lineHeight: 1.3,
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                    title={post.caption}
                  >
                    {post.caption || 'No caption text.'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
