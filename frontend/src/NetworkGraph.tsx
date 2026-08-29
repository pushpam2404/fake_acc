import React, { useEffect, useState, useRef, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, ShieldAlert, Cpu, Play, CheckCircle2, Move } from 'lucide-react';

interface Node {
  id: string;
  label: string;
  type: string;
  role?: string;
  risk_score: number;
  centrality: number;
  x: number;
  y: number;
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
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const draggingNodeRef = useRef<string | null>(null);
  const dragOffsetRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const panStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const width = 720;
  const height = 460;
  const centerX = width / 2;
  const centerY = height / 2;

  // Exact screen-to-SVG viewBox coordinate transformation
  const getSvgCoordinates = useCallback((clientX: number, clientY: number) => {
    if (!svgRef.current) return { x: centerX, y: centerY };
    const pt = svgRef.current.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const ctm = svgRef.current.getScreenCTM();
    if (!ctm) return { x: centerX, y: centerY };
    const transformed = pt.matrixTransform(ctm.inverse());
    return { x: transformed.x, y: transformed.y };
  }, [centerX, centerY]);

  // Initialize node constellation
  const initializeGraph = useCallback(() => {
    if (!data || !data.nodes || !data.nodes.length) return;

    const rawNodes = [...data.nodes];
    const targetIdx = rawNodes.findIndex((n) => n.type === 'target');
    const otherNodes = rawNodes.filter((_, idx) => idx !== targetIdx);

    const initializedNodes: Node[] = [];

    // Target node at center
    if (targetIdx !== -1) {
      initializedNodes.push({
        ...rawNodes[targetIdx],
        x: centerX,
        y: centerY,
        vx: 0,
        vy: 0,
      });
    }

    // Distribute other nodes in an aesthetic orbit
    const numOthers = otherNodes.length;
    const baseRadius = 145;

    otherNodes.forEach((node, i) => {
      const angle = (i / numOthers) * 2 * Math.PI - Math.PI / 2;
      const radialOffset = (i % 2 === 0 ? 25 : -25) + (node.centrality || 0) * 30;
      const r = baseRadius + radialOffset;

      initializedNodes.push({
        ...node,
        x: centerX + Math.cos(angle) * r,
        y: centerY + Math.sin(angle) * r,
        vx: 0,
        vy: 0,
      });
    });

    // Run initial physics relaxation
    for (let iter = 0; iter < 70; iter++) {
      for (let i = 0; i < initializedNodes.length; i++) {
        for (let j = i + 1; j < initializedNodes.length; j++) {
          const n1 = initializedNodes[i];
          const n2 = initializedNodes[j];
          const dx = n1.x - n2.x;
          const dy = n1.y - n2.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
          const minDist = 100;

          if (dist < minDist) {
            const overlap = (minDist - dist) / dist;
            const fx = dx * overlap * 0.45;
            const fy = dy * overlap * 0.45;

            if (n1.type !== 'target') {
              n1.x += fx;
              n1.y += fy;
            }
            if (n2.type !== 'target') {
              n2.x -= fx;
              n2.y -= fy;
            }
          }
        }
      }

      data.edges.forEach((edge) => {
        const s = initializedNodes.find((n) => n.id === edge.source);
        const t = initializedNodes.find((n) => n.id === edge.target);
        if (s && t) {
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
          const desiredDist = 135;
          const spring = (dist - desiredDist) * 0.04;

          const fx = (dx / dist) * spring;
          const fy = (dy / dist) * spring;

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

      initializedNodes.forEach((node) => {
        node.x = Math.max(50, Math.min(width - 50, node.x));
        node.y = Math.max(45, Math.min(height - 45, node.y));
      });
    }

    setNodes(initializedNodes);
    setPan({ x: 0, y: 0 });
    setZoom(1);
  }, [data, centerX, centerY]);

  useEffect(() => {
    initializeGraph();
  }, [initializeGraph]);

  // Smooth auto-arrange relaxation tick
  const runPhysicsTick = useCallback(() => {
    setNodes((prev) => {
      const next = prev.map((n) => ({ ...n }));
      const draggingId = draggingNodeRef.current;

      for (let i = 0; i < next.length; i++) {
        for (let j = i + 1; j < next.length; j++) {
          const n1 = next[i];
          const n2 = next[j];
          const dx = n1.x - n2.x;
          const dy = n1.y - n2.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
          const minDist = 110;

          if (dist < minDist) {
            const overlap = (minDist - dist) / dist;
            const fx = dx * overlap * 0.25;
            const fy = dy * overlap * 0.25;

            if (n1.id !== draggingId) {
              n1.x = Math.max(45, Math.min(width - 45, n1.x + fx));
              n1.y = Math.max(45, Math.min(height - 45, n1.y + fy));
            }
            if (n2.id !== draggingId) {
              n2.x = Math.max(45, Math.min(width - 45, n2.x - fx));
              n2.y = Math.max(45, Math.min(height - 45, n2.y - fy));
            }
          }
        }
      }

      data.edges.forEach((edge) => {
        const s = next.find((n) => n.id === edge.source);
        const t = next.find((n) => n.id === edge.target);
        if (s && t) {
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
          const desiredDist = 130;
          const spring = (dist - desiredDist) * 0.025;

          const fx = (dx / dist) * spring;
          const fy = (dy / dist) * spring;

          if (s.id !== draggingId) {
            s.x = Math.max(45, Math.min(width - 45, s.x + fx));
            s.y = Math.max(45, Math.min(height - 45, s.y + fy));
          }
          if (t.id !== draggingId) {
            t.x = Math.max(45, Math.min(width - 45, t.x - fx));
            t.y = Math.max(45, Math.min(height - 45, t.y - fy));
          }
        }
      });

      return next;
    });
  }, [data.edges]);

  const handleAutoArrange = () => {
    setIsSimulating(true);
    let count = 0;
    const interval = setInterval(() => {
      runPhysicsTick();
      count++;
      if (count > 25) {
        clearInterval(interval);
        setIsSimulating(false);
      }
    }, 25);
  };

  // Node Drag Handler (Uses exact SVG matrix transform for 1:1 tracking)
  const handlePointerDownNode = (e: React.PointerEvent, nodeId: string) => {
    e.stopPropagation();
    e.preventDefault();
    const node = nodes.find((n) => n.id === nodeId);
    if (!node) return;

    draggingNodeRef.current = nodeId;
    const svgCoords = getSvgCoordinates(e.clientX, e.clientY);
    dragOffsetRef.current = {
      x: svgCoords.x - node.x,
      y: svgCoords.y - node.y,
    };
    setSelectedNode(node);

    // Capture pointer events on the window for smooth dragging outside element bounds
    const handleWindowPointerMove = (ev: PointerEvent) => {
      if (!draggingNodeRef.current) return;
      const coords = getSvgCoordinates(ev.clientX, ev.clientY);
      const newX = coords.x - dragOffsetRef.current.x;
      const newY = coords.y - dragOffsetRef.current.y;

      setNodes((prev) =>
        prev.map((n) =>
          n.id === draggingNodeRef.current
            ? {
                ...n,
                x: Math.max(25, Math.min(width - 25, newX)),
                y: Math.max(25, Math.min(height - 25, newY)),
              }
            : n
        )
      );
    };

    const handleWindowPointerUp = () => {
      draggingNodeRef.current = null;
      window.removeEventListener('pointermove', handleWindowPointerMove);
      window.removeEventListener('pointerup', handleWindowPointerUp);
      window.removeEventListener('pointercancel', handleWindowPointerUp);
    };

    window.addEventListener('pointermove', handleWindowPointerMove);
    window.addEventListener('pointerup', handleWindowPointerUp);
    window.addEventListener('pointercancel', handleWindowPointerUp);
  };

  // Background Pan Handler
  const handlePointerDownCanvas = (e: React.PointerEvent) => {
    if (draggingNodeRef.current) return;
    setIsPanning(true);
    panStartRef.current = {
      x: e.clientX - pan.x,
      y: e.clientY - pan.y,
    };
    setSelectedNode(null);

    const handleWindowPanMove = (ev: PointerEvent) => {
      setPan({
        x: ev.clientX - panStartRef.current.x,
        y: ev.clientY - panStartRef.current.y,
      });
    };

    const handleWindowPanUp = () => {
      setIsPanning(false);
      window.removeEventListener('pointermove', handleWindowPanMove);
      window.removeEventListener('pointerup', handleWindowPanUp);
      window.removeEventListener('pointercancel', handleWindowPanUp);
    };

    window.addEventListener('pointermove', handleWindowPanMove);
    window.addEventListener('pointerup', handleWindowPanUp);
    window.addEventListener('pointercancel', handleWindowPanUp);
  };

  // Mouse wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.08 : -0.08;
    setZoom((z) => Math.min(1.8, Math.max(0.6, z + delta)));
  };

  const getNodeColor = (risk: number, type: string) => {
    if (type === 'target') return '#8b5cf6'; // Violet for target subject
    if (risk > 70) return '#ef4444'; // Crimson Red for confirmed bots
    if (risk >= 30) return '#f59e0b'; // Amber for suspicious nodes
    return '#10b981'; // Emerald Green for genuine humans
  };

  const getEdgeThreatLevel = (edge: Edge) => {
    const reason = edge.reason.toLowerCase();
    if (reason.includes('subnet') || reason.includes('honeypot') || reason.includes('fingerprint') || reason.includes('botnet') || reason.includes('retweet ring')) {
      return 'CRITICAL';
    }
    if (reason.includes('high-frequency') || reason.includes('anomaly') || reason.includes('engagement circle') || reason.includes('promoter')) {
      return 'SUSPICIOUS';
    }
    return 'ORGANIC';
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
          flexWrap: 'wrap',
          gap: '0.5rem',
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

        {/* Metrics Badges & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <div
            style={{
              display: 'flex',
              gap: '0.5rem',
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

          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              onClick={handleAutoArrange}
              disabled={isSimulating}
              style={{
                background: 'var(--bg-input)',
                border: '1px solid var(--border-default)',
                borderRadius: '4px',
                padding: '3px 7px',
                fontSize: '0.72rem',
                color: 'var(--text-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
                cursor: 'pointer',
              }}
              title="Auto-arrange network layout"
            >
              <Play size={10} color="#8b5cf6" /> Auto-Arrange
            </button>
            <button
              onClick={() => setZoom((z) => Math.min(1.8, z + 0.15))}
              style={{
                background: 'var(--bg-input)',
                border: '1px solid var(--border-default)',
                borderRadius: '4px',
                padding: '3px 6px',
                cursor: 'pointer',
              }}
              title="Zoom In"
            >
              <ZoomIn size={12} />
            </button>
            <button
              onClick={() => setZoom((z) => Math.max(0.6, z - 0.15))}
              style={{
                background: 'var(--bg-input)',
                border: '1px solid var(--border-default)',
                borderRadius: '4px',
                padding: '3px 6px',
                cursor: 'pointer',
              }}
              title="Zoom Out"
            >
              <ZoomOut size={12} />
            </button>
            <button
              onClick={initializeGraph}
              style={{
                background: 'var(--bg-input)',
                border: '1px solid var(--border-default)',
                borderRadius: '4px',
                padding: '3px 6px',
                cursor: 'pointer',
              }}
              title="Reset Layout & Centering"
            >
              <RotateCcw size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* Interactive Cyber Canvas */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: `${height}px`,
          background: 'radial-gradient(ellipse at center, #0f172a 0%, #080d1a 100%)',
          borderRadius: '8px',
          overflow: 'hidden',
          border: '1px solid #1e293b',
          cursor: isPanning ? 'grabbing' : 'grab',
          userSelect: 'none',
          touchAction: 'none',
        }}
        onPointerDown={handlePointerDownCanvas}
        onWheel={handleWheel}
      >
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox={`0 0 ${width} ${height}`}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            overflow: 'visible',
            pointerEvents: 'auto',
          }}
        >
          <defs>
            <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.12" />
              <stop offset="60%" stopColor="#6366f1" stopOpacity="0.04" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
            </radialGradient>

            <filter id="threatGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <filter id="targetAura" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Radar Circles */}
          <circle cx={centerX} cy={centerY} r={75} fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
          <circle cx={centerX} cy={centerY} r={155} fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="4 4" />
          <circle cx={centerX} cy={centerY} r={230} fill="none" stroke="#0f172a" strokeWidth="1" />
          <circle cx={centerX} cy={centerY} r={155} fill="url(#radarGlow)" />

          {/* Crosshair Center Lines */}
          <line x1={centerX - 260} y1={centerY} x2={centerX + 260} y2={centerY} stroke="#1e293b" strokeWidth="0.8" opacity="0.3" />
          <line x1={centerX} y1={centerY - 190} x2={centerX} y2={centerY + 190} stroke="#1e293b" strokeWidth="0.8" opacity="0.3" />

          {/* Render Graph Edges */}
          {data.edges.map((edge, idx) => {
            const sourceNode = nodes.find((n) => n.id === edge.source);
            const targetNode = nodes.find((n) => n.id === edge.target);

            if (!sourceNode || !targetNode) return null;

            const isHovered = hoveredEdge === edge;
            const isHighlighted =
              (hoveredNode && (hoveredNode.id === edge.source || hoveredNode.id === edge.target)) ||
              (selectedNode && (selectedNode.id === edge.source || selectedNode.id === edge.target));

            const threatLevel = getEdgeThreatLevel(edge);
            const isCIB = threatLevel === 'CRITICAL';
            const isOrganic = threatLevel === 'ORGANIC';

            let strokeColor = '#334155';
            if (isHovered) {
              strokeColor = isOrganic ? '#34d399' : isCIB ? '#f43f5e' : '#fbbf24';
            } else if (isHighlighted) {
              strokeColor = isOrganic ? '#10b981' : isCIB ? '#ef4444' : '#f59e0b';
            } else if (isCIB) {
              strokeColor = 'rgba(239, 68, 68, 0.45)';
            } else if (isOrganic) {
              strokeColor = 'rgba(52, 211, 153, 0.25)';
            }

            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={sourceNode.x}
                  y1={sourceNode.y}
                  x2={targetNode.x}
                  y2={targetNode.y}
                  stroke={strokeColor}
                  strokeWidth={isHovered ? 3.5 : isHighlighted ? 2.5 : isCIB ? 1.6 : 1.2}
                  strokeDasharray={isCIB ? '4 3' : undefined}
                  opacity={isHovered || isHighlighted ? 1 : 0.7}
                  onMouseEnter={() => setHoveredEdge(edge)}
                  onMouseLeave={() => setHoveredEdge(null)}
                  style={{ cursor: 'pointer', transition: 'stroke 0.2s, stroke-width 0.2s' }}
                />
              </g>
            );
          })}

          {/* Render Graph Nodes — Every node is draggable */}
          {nodes.map((node) => {
            const isTarget = node.type === 'target';
            const radius = isTarget ? 16 : 10 + (node.centrality * 10);
            const color = getNodeColor(node.risk_score, node.type);
            const isHovered = hoveredNode?.id === node.id;
            const isSelected = selectedNode?.id === node.id;
            const isHighRisk = node.risk_score > 70;

            return (
              <g
                key={`node-${node.id}`}
                onPointerDown={(e) => handlePointerDownNode(e, node.id)}
                onMouseEnter={() => setHoveredNode(node)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: 'grab' }}
              >
                {/* Outer animated halo for target node */}
                {isTarget && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={radius + 9}
                    fill="none"
                    stroke="#8b5cf6"
                    strokeWidth="1.5"
                    opacity="0.5"
                    strokeDasharray="4 3"
                    style={{ animation: 'spin 12s linear infinite' }}
                  />
                )}

                {/* Threat pulse halo for high-risk bot nodes */}
                {isHighRisk && !isTarget && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={radius + 6}
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth="1.2"
                    opacity="0.6"
                  />
                )}

                {/* Primary Node Circle */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={radius}
                  fill={color}
                  stroke={isSelected ? '#ffffff' : isHovered ? '#f8fafc' : '#0f172a'}
                  strokeWidth={isSelected ? 3 : isHovered ? 2.5 : 2}
                  filter={isTarget ? 'url(#targetAura)' : isHighRisk ? 'url(#threatGlow)' : undefined}
                />

                {/* Node Pill Label Backdrop */}
                <rect
                  x={node.x - (node.label.length * 3.3 + 9)}
                  y={node.y + radius + 4}
                  width={node.label.length * 6.6 + 18}
                  height={16}
                  rx={4}
                  fill="rgba(15, 23, 42, 0.9)"
                  stroke={isTarget ? '#8b5cf6' : isHighRisk ? '#ef4444' : '#334155'}
                  strokeWidth={isTarget || isSelected ? '1' : '0.7'}
                />

                {/* Node Label Text */}
                <text
                  x={node.x}
                  y={node.y + radius + 16}
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

        {/* Hover/Selected Edge Tooltip Card — Positioned neatly at top-left so it never covers bottom nodes */}
        {hoveredEdge && !hoveredNode && (
          (() => {
            const level = getEdgeThreatLevel(hoveredEdge);
            const isOrganic = level === 'ORGANIC';
            const isCritical = level === 'CRITICAL';

            const border = isOrganic ? '1px solid #10b981' : isCritical ? '1px solid #ef4444' : '1px solid #f59e0b';
            const badgeBg = isOrganic ? 'rgba(16, 185, 129, 0.25)' : isCritical ? 'rgba(239, 68, 68, 0.25)' : 'rgba(245, 158, 11, 0.25)';
            const badgeColor = isOrganic ? '#86efac' : isCritical ? '#fca5a5' : '#fde68a';

            return (
              <div
                style={{
                  position: 'absolute',
                  top: '12px',
                  left: '12px',
                  background: 'rgba(15, 23, 42, 0.95)',
                  border: border,
                  borderRadius: '6px',
                  padding: '8px 12px',
                  fontSize: '0.75rem',
                  color: '#f8fafc',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.6)',
                  pointerEvents: 'none',
                  maxWidth: '320px',
                  backdropFilter: 'blur(4px)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    {isOrganic ? <CheckCircle2 size={13} color="#34d399" /> : <ShieldAlert size={13} color="#f87171" />}
                    <span style={{ fontWeight: 700, fontSize: '0.8rem' }}>
                      @{hoveredEdge.source} ⟷ @{hoveredEdge.target}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: '0.62rem',
                      padding: '1px 5px',
                      borderRadius: '3px',
                      background: badgeBg,
                      color: badgeColor,
                      fontWeight: 700,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {level}
                  </span>
                </div>
                <div style={{ color: '#cbd5e1', fontSize: '0.72rem', marginTop: '2px', lineHeight: 1.35 }}>
                  Relation: <span style={{ color: '#ffffff', fontWeight: 600 }}>{hoveredEdge.reason}</span>
                </div>
              </div>
            );
          })()
        )}

        {/* Hover / Selected Node Tooltip Card */}
        {(hoveredNode || selectedNode) && (
          (() => {
            const n = hoveredNode || selectedNode;
            if (!n) return null;
            const isHigh = n.risk_score > 70;
            const isMed = n.risk_score >= 30;

            return (
              <div
                style={{
                  position: 'absolute',
                  top: '12px',
                  left: '12px',
                  background: 'rgba(15, 23, 42, 0.95)',
                  border: `1px solid ${getNodeColor(n.risk_score, n.type)}`,
                  borderRadius: '6px',
                  padding: '8px 12px',
                  fontSize: '0.75rem',
                  color: '#f8fafc',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.6)',
                  pointerEvents: 'none',
                  minWidth: '220px',
                  backdropFilter: 'blur(4px)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                  <b style={{ color: '#ffffff', fontSize: '0.85rem' }}>{n.label}</b>
                  <span
                    style={{
                      fontSize: '0.65rem',
                      padding: '1px 6px',
                      borderRadius: '3px',
                      background: isHigh ? 'rgba(239, 68, 68, 0.25)' : isMed ? 'rgba(245, 158, 11, 0.25)' : 'rgba(16, 185, 129, 0.25)',
                      color: isHigh ? '#fca5a5' : isMed ? '#fde68a' : '#86efac',
                      fontWeight: 700,
                    }}
                  >
                    {n.type.toUpperCase()}
                  </span>
                </div>
                <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>
                  Role: <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{n.role || 'Network Node'}</span>
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '4px', fontSize: '0.7rem', color: '#cbd5e1' }}>
                  <div>Risk: <b style={{ color: isHigh ? '#f87171' : isMed ? '#fbbf24' : '#34d399' }}>{n.risk_score}%</b></div>
                  <div>Centrality: <b className="mono">{n.centrality}</b></div>
                </div>
              </div>
            );
          })()
        )}

        {/* Interaction Hint */}
        <div
          style={{
            position: 'absolute',
            bottom: '8px',
            right: '10px',
            fontSize: '0.65rem',
            color: '#64748b',
            pointerEvents: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <Move size={10} /> Drag any node to reposition • Drag canvas to pan
        </div>
      </div>

      {/* Graph Legend */}
      <div
        style={{
          display: 'flex',
          gap: '1.2rem',
          justifyContent: 'center',
          marginTop: '0.85rem',
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
