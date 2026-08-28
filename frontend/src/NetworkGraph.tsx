import React, { useEffect, useState } from 'react';

interface Node {
  id: string;
  label: string;
  type: string;
  risk_score: number;
  centrality: number;
  x?: number;
  y?: number;
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

  const width = 500;
  const height = 350;

  useEffect(() => {
    if (!data || !data.nodes.length) return;

    // 1. Initialize node positions randomly near the center
    const tempNodes = data.nodes.map((node) => ({
      ...node,
      x: width / 2 + (Math.random() - 0.5) * 80,
      y: height / 2 + (Math.random() - 0.5) * 80,
    }));

    const k = Math.sqrt((width * height) / tempNodes.length) * 0.75;
    const iterations = 80;
    const cooling = 0.92;
    let temp = 30.0;

    // 2. Simple Fruchterman-Reingold Force-Directed Layout Loop
    for (let iter = 0; iter < iterations; iter++) {
      // Calculate Repulsion forces between all nodes
      for (let i = 0; i < tempNodes.length; i++) {
        const nodeA = tempNodes[i];
        nodeA.x = nodeA.x || width / 2;
        nodeA.y = nodeA.y || height / 2;
        
        let dxSum = 0;
        let dySum = 0;

        for (let j = 0; j < tempNodes.length; j++) {
          if (i === j) continue;
          const nodeB = tempNodes[j];
          nodeB.x = nodeB.x || width / 2;
          nodeB.y = nodeB.y || height / 2;

          const dx = nodeA.x - nodeB.x;
          const dy = nodeA.y - nodeB.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;

          if (dist < 150) {
            // Repulsion force
            const force = (k * k) / dist;
            dxSum += (dx / dist) * force;
            dySum += (dy / dist) * force;
          }
        }
        
        nodeA.x += (dxSum / tempNodes.length) * temp;
        nodeA.y += (dySum / tempNodes.length) * temp;
      }

      // Calculate Attraction forces along edges
      data.edges.forEach((edge) => {
        const sourceNode = tempNodes.find((n) => n.id === edge.source);
        const targetNode = tempNodes.find((n) => n.id === edge.target);

        if (sourceNode && targetNode && sourceNode.x && sourceNode.y && targetNode.x && targetNode.y) {
          const dx = sourceNode.x - targetNode.x;
          const dy = sourceNode.y - targetNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;

          const force = (dist * dist) / k;
          const fx = (dx / dist) * force * 0.15;
          const fy = (dy / dist) * force * 0.15;

          sourceNode.x -= fx * temp;
          sourceNode.y -= fy * temp;
          targetNode.x += fx * temp;
          targetNode.y += fy * temp;
        }
      });

      // Gravity force pulling towards canvas center
      tempNodes.forEach((node) => {
        if (node.x && node.y) {
          const dx = node.x - width / 2;
          const dy = node.y - height / 2;
          node.x -= dx * 0.05;
          node.y -= dy * 0.05;
          
          // Boundaries clamping
          node.x = Math.max(25, Math.min(width - 25, node.x));
          node.y = Math.max(25, Math.min(height - 25, node.y));
        }
      });

      temp *= cooling;
    }

    setNodes(tempNodes);
  }, [data]);

  const getNodeColor = (risk: number, type: string) => {
    if (type === 'target') return '#9333ea'; // Purple for target profile
    if (risk > 70) return '#dc2626'; // Red for bots
    if (risk >= 30) return '#d97706'; // Amber for suspicious
    return '#16a34a'; // Green for genuine human
  };

  return (
    <div className="network-graph-container" style={{ margin: '1.25rem 0', padding: '1rem', border: '1px solid var(--border-default)', borderRadius: '6px', background: 'rgba(15, 23, 42, 0.03)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h4 style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Network Co-occurrence Graph Mapping
        </h4>
        <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
          <div>Density: <span className="mono">{data.density || 0.0}</span></div>
          <div>Cliques: <span className="mono">{data.clique_count || 1}</span></div>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', height: `${height}px`, background: '#0f172a', borderRadius: '4px', overflow: 'hidden', border: '1px solid #334155' }}>
        <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
          {/* Render connection edges */}
          {data.edges.map((edge, idx) => {
            const sourceNode = nodes.find((n) => n.id === edge.source);
            const targetNode = nodes.find((n) => n.id === edge.target);

            if (!sourceNode || !targetNode || !sourceNode.x || !sourceNode.y || !targetNode.x || !targetNode.y) return null;

            const isHovered = hoveredEdge === edge;

            return (
              <line
                key={idx}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={isHovered ? '#f43f5e' : '#475569'}
                strokeWidth={isHovered ? 2.5 : 1}
                strokeDasharray={edge.reason.includes('Honeypot') || edge.reason.includes('Similarity') ? '4 4' : undefined}
                onMouseEnter={() => setHoveredEdge(edge)}
                onMouseLeave={() => setHoveredEdge(null)}
                style={{ cursor: 'pointer', transition: 'stroke 0.2s' }}
              />
            );
          })}

          {/* Render nodes */}
          {nodes.map((node) => {
            if (!node.x || !node.y) return null;

            // Target node is larger
            const radius = node.type === 'target' ? 12 : 7 + (node.centrality * 12);
            const color = getNodeColor(node.risk_score, node.type);

            return (
              <g key={node.id}>
                {/* Glow ring for bot nodes */}
                {node.risk_score > 70 && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={radius + 4}
                    fill="none"
                    stroke={color}
                    strokeWidth={1}
                    opacity={0.3}
                    style={{ animation: 'pulse 2s infinite' }}
                  />
                )}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={radius}
                  fill={color}
                  stroke="#1e293b"
                  strokeWidth={2}
                />
                <text
                  x={node.x}
                  y={node.y - radius - 4}
                  textAnchor="middle"
                  fill="#f1f5f9"
                  fontSize="7.5px"
                  fontWeight={node.type === 'target' ? 'bold' : 'normal'}
                  style={{ pointerEvents: 'none', userSelect: 'none', paintOrder: 'stroke', stroke: '#0f172a', strokeWidth: 1.5 }}
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover info panel (Tooltip) */}
        {hoveredEdge && (
          <div style={{ position: 'absolute', bottom: '8px', left: '8px', right: '8px', background: 'rgba(30, 41, 59, 0.95)', border: '1px solid #475569', borderRadius: '3px', padding: '6px 10px', fontSize: '0.75rem', color: '#f8fafc', display: 'flex', gap: '0.5rem', justifyContent: 'space-between', pointerEvents: 'none' }}>
            <span>Relation: <b>@{hoveredEdge.source}</b> ➔ <b>@{hoveredEdge.target}</b></span>
            <span style={{ color: '#fb7185', fontWeight: 600 }}>{hoveredEdge.reason}</span>
          </div>
        )}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '0.65rem', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#9333ea' }} />
          <span>Target Profile</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#dc2626' }} />
          <span>Coordinated Bot</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#d97706' }} />
          <span>Suspicious Node</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#16a34a' }} />
          <span>Genuine Human</span>
        </div>
      </div>
    </div>
  );
}
