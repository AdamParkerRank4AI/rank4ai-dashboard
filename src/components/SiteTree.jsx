import { useState } from 'react';

function TreeNode({ node, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div style={{ marginLeft: depth > 0 ? 20 : 0 }}>
      <div
        onClick={() => hasChildren && setExpanded(!expanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '4px 8px',
          cursor: hasChildren ? 'pointer' : 'default',
          borderRadius: 4,
          fontSize: 12,
          color: '#e5e7eb',
          background: depth === 0 ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
        }}
        onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.05)'}
        onMouseLeave={(e) => e.target.style.background = depth === 0 ? 'rgba(59, 130, 246, 0.1)' : 'transparent'}
      >
        {hasChildren ? (
          <span style={{ color: '#6b7280', fontSize: 10, width: 12, textAlign: 'center' }}>
            {expanded ? '▼' : '▶'}
          </span>
        ) : (
          <span style={{ color: '#374151', fontSize: 10, width: 12, textAlign: 'center' }}>●</span>
        )}
        <span style={{ color: depth === 0 ? '#3b82f6' : '#d1d5db' }}>
          {node.name === '/' ? '/ (homepage)' : node.name}
        </span>
        {hasChildren && (
          <span style={{ color: '#4b5563', fontSize: 10 }}>
            ({node.children.length})
          </span>
        )}
      </div>
      {expanded && hasChildren && (
        <div style={{ borderLeft: '1px solid #1f2937', marginLeft: 14 }}>
          {node.children.map((child, i) => (
            <TreeNode key={i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function SiteTree({ tree }) {
  if (!tree) return <p style={{ color: '#6b7280', fontSize: 12 }}>No site tree data available</p>;

  return (
    <div style={{ fontFamily: 'monospace', maxHeight: 500, overflowY: 'auto' }}>
      <TreeNode node={tree} />
    </div>
  );
}
