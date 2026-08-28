import React, { useEffect, useState, useRef } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, ShieldAlert, Cpu } from 'lucide-react';

interface Node {
  id: string;
  label: string;
  type: string;
  role?: string;
  risk_score: number;
  centrality: number;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface Edge {
  source: string;
  target: string;
  reason: string;
}

interface NetworkGraphProps {
  data: {
    nodes: Node[];
    edges: Edge[];
    density?: number;
    clique_count?: number;
  };
}

export function NetworkGraph({ data }: NetworkGraphProps) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [hoveredEdge, setHoveredEdge] = useState<Edge | null>(null);
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);

  const width = 640;
  const height = 430;
  const centerX = width / 2;
  const centerY = height / 2;

  // Initialize and run radial force layout
  useEffect(() => {
    if (!data || !data.nodes || !data.nodes.length) return;

    const rawNodes = [...data.nodes];
    const targetIdx = rawNodes.findIndex((n) => n.type === 'target');
    const otherNodes = rawNodes.filter((_, idx) => idx !== targetIdx);

    // 1. Radial Constellation Layout
    // Place target in absolute center, and distribute others in a spacious circle
    const initializedNodes: Node[] = [];

    if (targetIdx !== -1) {
      initializedNodes.push({
        ...rawNodes[targetIdx],
        x: centerX,
        y: centerY,
        vx: 0,
        vy: 0,
      });
    }

    const numOthers = otherNodes.length;
    const baseRadius = 135;

    otherNodes.forEach((node, i) => {
      const angle = (i / numOthers) * 2 * Math.PI - Math.PI / 2;
      // Stagger radius to create an organic, realistic network topology
      const radialOffset = (i % 2 === 0 ? 30 : -20) + (node.centrality || 0) * 25;
      const r = baseRadius + radialOffset;

      initializedNodes.push({
        ...node,
        x: centerX + Math.cos(angle) * r,
        y: centerY + Math.sin(angle) * r,
        vx: 0,
        vy: 0,
      });
    });

    // 2. Multi-iteration Physics Relaxation (Prevent overlap & equalize spacing)
    const iterations = 60;
    for (let iter = 0; iter < iterations; iter++) {
      // Repulsion between all node pairs (Anti-clustering)
      for (let i = 0; i < initializedNodes.length; i++) {
        for (let j = i + 1; j < initializedNodes.length; j++) {
          const n1 = initializedNodes[i];
          const n2 = initializedNodes[j];

          const dx = (n1.x || centerX) - (n2.x || centerX);
          const dy = (n1.y || centerY) - (n2.y || centerY);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
          const minDist = 95; // Minimum space between nodes

          if (dist < minDist) {
            const overlap = (minDist - dist) / dist;
            const forceX = dx * overlap * 0.4;
            const forceY = dy * overlap * 0.4;

            if (n1.type !== 'target') {
              n1.x = (n1.x || centerX) + forceX;
              n1.y = (n1.y || centerY) + forceY;
            }
            if (n2.type !== 'target') {
              n2.x = (n2.x || centerX) - forceX;
              n2.y = (n2.y || centerY) - forceY;
            }
          }
        }
      }

      // Spring attraction along edges
      data.edges.forEach((edge) => {
        const s = initializedNodes.find((n) => n.id === edge.source);
        const t = initializedNodes.find((n) => n.id === edge.target);
        if (s && t && s.x && s.y && t.x && t.y) {
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
          const desiredDist = 130;
          const springForce = (dist - desiredDist) * 0.04;

          const fx = (dx / dist) * springForce;
          const fy = (dy / dist) * springForce;

          if (s.type !== 'target') {
            s.x += fx;
            s.y += fy;
          }
          if (t.type !== 'target') {
            t.x -= fx;
            t.y -= fy;
          }
        }
      });

      // Keep within canvas bounds
      initializedNodes.forEach((node) => {
        if (node.type === 'target') {
          node.x = centerX;
          node.y = centerY;
        } else {
          node.x = Math.max(55, Math.min(width - 55, node.x || centerX));
          node.y = Math.max(45, Math.min(height - 45, node.y || centerY));
        }
      });
    }

    setNodes(initializedNodes);
  }, [data]);

  // Interactive Node Dragging Handlers
  const handleMouseDown = (nodeId: string) => {
    setDraggingNodeId(nodeId);
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!draggingNodeId || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const scaleX = width / rect.width;
    const scaleY = height / rect.height;

    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;

    setNodes((prevNodes) =>
      prevNodes.map((n) =>
        n.id === draggingNodeId
          ? {
              ...n,
              x: Math.max(35, Math.min(width - 35, mouseX)),
              y: Math.max(35, Math.min(height - 35, mouseY)),
            }
          : n
      )
    );
  };

  const handleMouseUp = () => {
    setDraggingNodeId(null);
  };

  const getNodeColor = (risk: number, type: string) => {
    if (type === 'target') return '#8b5cf6'; // Violet for target subject
    if (risk > 70) return '#ef4444'; // Crimson Red for confirmed bots
    if (risk >= 30) return '#f59e0b'; // Amber for suspicious nodes
    return '#10b981'; // Emerald Green for genuine humans
  };

  return (
    <div
      className="network-graph-container"
      style={{
        margin: '1.25rem 0',
        padding: '1.1rem',
        border: '1px solid var(--border-default)',
        borderRadius: '8px',
        background: 'var(--bg-card)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
      }}
    >
      {/* Header Info */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.85rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Cpu size={16} color="#8b5cf6" />
          <h4
            style={{
              margin: 0,
              fontSize: '0.85rem',
              color: 'var(--text-primary)',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              fontWeight: 700,
            }}
          >
            Coordinated Threat Network Topology
          </h4>
        </div>

        {/* Metrics Badges & Zoom Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div
            style={{
              display: 'flex',
              gap: '0.6rem',
              fontSize: '0.72rem',
              color: 'var(--text-secondary)',
              background: 'rgba(15, 23, 42, 0.04)',
              padding: '3px 8px',
              borderRadius: '4px',
              border: '1px solid var(--border-default)',
            }}
          >
            <div>
              Density: <span className="mono" style={{ fontWeight: 600 }}>{data.density ?? 0.0}</span>
            </div>
            <div>•</div>
            <div>
              Cliques: <span className="mono" style={{ fontWeight: 600 }}>{data.clique_count ?? 1}</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '2px', marginLeft: '0.25rem' }}>
            <button
              onClick={() => setZoom((z) => Math.min(1.4, z + 0.1))}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-default)',
                borderRadius: '3px',
                padding: '2px 5px',
                cursor: 'pointer',
              }}
              title="Zoom In"
            >
              <ZoomIn size={13} />
            </button>
            <button
              onClick={() => setZoom((z) => Math.max(0.7, z - 0.1))}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-default)',
                borderRadius: '3px',
                padding: '2px 5px',
                cursor: 'pointer',
              }}
              title="Zoom Out"
            >
              <ZoomOut size={13} />
            </button>
            <button
              onClick={() => setZoom(1)}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-default)',
                borderRadius: '3px',
                padding: '2px 5px',
                cursor: 'pointer',
              }}
              title="Reset Layout View"
            >
              <RotateCcw size={13} />
            </button>
          </div>
        </div>
      </div>

      {/* Interactive Dark Cyber Canvas */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: `${height}px`,
          background: 'radial-gradient(ellipse at center, #111827 0%, #080d1a 100%)',
          borderRadius: '6px',
          overflow: 'hidden',
          border: '1px solid #1e293b',
          cursor: draggingNodeId ? 'grabbing' : 'default',
        }}
      >
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox={`0 0 ${width} ${height}`}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: 'center center',
            transition: draggingNodeId ? 'none' : 'transform 0.2s ease-out',
          }}
        >
          <defs>
            {/* Radial Radar Grid Pattern */}
            <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
            </radialGradient>

            {/* Glowing filter for high-risk threat nodes */}
            <filter id="threatGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background Concentric Radar Rings */}
          <circle cx={centerX} cy={centerY} r={65} fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
          <circle cx={centerX} cy={centerY} r={135} fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="4 4" />
          <circle cx={centerX} cy={centerY} r={200} fill="none" stroke="#0f172a" strokeWidth="1" />
          <circle cx={centerX} cy={centerY} r={135} fill="url(#radarGlow)" />

          {/* Crosshair Center Lines */}
          <line x1={centerX - 220} y1={centerY} x2={centerX + 220} y2={centerY} stroke="#1e293b" strokeWidth="0.8" opacity="0.4" />
          <line x1={centerX} y1={centerY - 160} x2={centerX} y2={centerY + 160} stroke="#1e293b" strokeWidth="0.8" opacity="0.4" />

          {/* Render Graph Edges (Connections) */}
          {data.edges.map((edge, idx) => {
            const sourceNode = nodes.find((n) => n.id === edge.source);
            const targetNode = nodes.find((n) => n.id === edge.target);

            if (!sourceNode || !targetNode || sourceNode.x === undefined || sourceNode.y === undefined || targetNode.x === undefined || targetNode.y === undefined) {
              return null;
            }

            const isHovered = hoveredEdge === edge;
            const isHighlighted =
              hoveredNode && (hoveredNode.id === edge.source || hoveredNode.id === edge.target);

            const isCIB = edge.reason.includes('Subnet') || edge.reason.includes('Honeypot') || edge.reason.includes('Fingerprint');

            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={sourceNode.x}
                  y1={sourceNode.y}
                  x2={targetNode.x}
                  y2={targetNode.y}
                  stroke={
                    isHovered
                      ? '#f43f5e'
                      : isHighlighted
                      ? '#ec4899'
                      : isCIB
                      ? '#b91c1c'
                      : '#334155'
                  }
                  strokeWidth={isHovered ? 3 : isHighlighted ? 2.2 : isCIB ? 1.5 : 1}
                  strokeDasharray={isCIB ? '4 3' : undefined}
                  opacity={isHovered || isHighlighted ? 1 : 0.65}
                  onMouseEnter={() => setHoveredEdge(edge)}
                  onMouseLeave={() => setHoveredEdge(null)}
                  style={{ cursor: 'pointer', transition: 'stroke 0.2s, stroke-width 0.2s' }}
                />
              </g>
            );
          })}

          {/* Render Graph Nodes */}
          {nodes.map((node) => {
            if (node.x === undefined || node.y === undefined) return null;

            const isTarget = node.type === 'target';
            const radius = isTarget ? 15 : 9 + (node.centrality * 10);
            const color = getNodeColor(node.risk_score, node.type);
            const isHovered = hoveredNode?.id === node.id;
            const isHighRisk = node.risk_score > 70;

            return (
              <g
                key={`node-${node.id}`}
                onMouseDown={() => handleMouseDown(node.id)}
                onMouseEnter={() => setHoveredNode(node)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: 'grab' }}
              >
                {/* Outer animated halo for target or bot clusters */}
                {isTarget && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={radius + 8}
                    fill="none"
                    stroke="#8b5cf6"
                    strokeWidth="1.5"
                    opacity="0.4"
                    strokeDasharray="4 3"
                    style={{ animation: 'spin 12s linear infinite' }}
                  />
                )}

                {isHighRisk && !isTarget && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={radius + 5}
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth="1"
                    opacity="0.5"
                  />
                )}

                {/* Primary Node Circle */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={radius}
                  fill={color}
                  stroke={isHovered ? '#ffffff' : '#0f172a'}
                  strokeWidth={isHovered ? 2.5 : 2}
                  filter={isHighRisk || isTarget ? 'url(#threatGlow)' : undefined}
                />

                {/* Node Pill Label Backdrop */}
                <rect
                  x={node.x - (node.label.length * 3.2 + 8)}
                  y={node.y + radius + 4}
                  width={node.label.length * 6.4 + 16}
                  height={15}
                  rx={3}
                  fill="rgba(15, 23, 42, 0.85)"
                  stroke={isTarget ? '#8b5cf6' : '#334155'}
                  strokeWidth="0.75"
                />

                {/* Node Label Text */}
                <text
                  x={node.x}
                  y={node.y + radius + 15}
                  textAnchor="middle"
                  fill="#f8fafc"
                  fontSize="8.5px"
                  fontFamily="ui-monospace, monospace"
                  fontWeight={isTarget ? '700' : '500'}
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover Edge Tooltip */}
        {hoveredEdge && !hoveredNode && (
          <div
            style={{
              position: 'absolute',
              bottom: '10px',
              left: '12px',
              right: '12px',
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid #dc2626',
              borderRadius: '5px',
              padding: '7px 12px',
              fontSize: '0.75rem',
              color: '#f8fafc',
              display: 'flex',
              gap: '0.5rem',
              justifyContent: 'space-between',
              alignItems: 'center',
              boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
              pointerEvents: 'none',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <ShieldAlert size={14} color="#f43f5e" />
              <span>
                <b>@{hoveredEdge.source}</b> ⟷ <b>@{hoveredEdge.target}</b>
              </span>
            </div>
            <span style={{ color: '#fb7185', fontWeight: 600, fontFamily: 'monospace' }}>
              {hoveredEdge.reason}
            </span>
          </div>
        )}

        {/* Hover Node Tooltip Card */}
        {hoveredNode && (
          <div
            style={{
              position: 'absolute',
              top: '10px',
              left: '12px',
              background: 'rgba(15, 23, 42, 0.95)',
              border: `1px solid ${getNodeColor(hoveredNode.risk_score, hoveredNode.type)}`,
              borderRadius: '5px',
              padding: '8px 12px',
              fontSize: '0.75rem',
              color: '#f8fafc',
              boxShadow: '0 4px 14px rgba(0,0,0,0.6)',
              pointerEvents: 'none',
              maxWidth: '260px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
              <b style={{ color: '#ffffff', fontSize: '0.85rem' }}>{hoveredNode.label}</b>
              <span
                style={{
                  fontSize: '0.65rem',
                  padding: '1px 5px',
                  borderRadius: '3px',
                  background: hoveredNode.risk_score > 70 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)',
                  color: hoveredNode.risk_score > 70 ? '#fca5a5' : '#86efac',
                  fontWeight: 600,
                }}
              >
                {hoveredNode.type.toUpperCase()}
              </span>
            </div>
            <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>
              Role: <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{hoveredNode.role || 'Network Node'}</span>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '4px', fontSize: '0.7rem', color: '#cbd5e1' }}>
              <div>Risk: <b style={{ color: hoveredNode.risk_score > 70 ? '#f87171' : '#34d399' }}>{hoveredNode.risk_score}%</b></div>
              <div>Degree Centrality: <b className="mono">{hoveredNode.centrality}</b></div>
            </div>
          </div>
        )}

        {/* Drag Hint */}
        <div
          style={{
            position: 'absolute',
            bottom: '8px',
            right: '10px',
            fontSize: '0.65rem',
            color: '#64748b',
            pointerEvents: 'none',
          }}
        >
          💡 Drag any node to reposition
        </div>
      </div>

      {/* Graph Legend */}
      <div
        style={{
          display: 'flex',
          gap: '1.2rem',
          justifyContent: 'center',
          marginTop: '0.8rem',
          fontSize: '0.72rem',
          color: 'var(--text-secondary)',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <div style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#8b5cf6' }} />
          <span>Investigated Subject</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <div style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#ef4444' }} />
          <span>Coordinated Bot / Puppet</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <div style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#f59e0b' }} />
          <span>Suspicious Cluster</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <div style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#10b981' }} />
          <span>Organic Human Peer</span>
        </div>
      </div>
    </div>
  );
}
